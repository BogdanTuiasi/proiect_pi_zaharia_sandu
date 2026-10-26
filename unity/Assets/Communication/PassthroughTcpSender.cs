using System;
using System.Collections.Generic;
using System.Globalization;
using System.Net.Sockets;
using System.IO;
using System.Text;
using System.Threading.Tasks;
using Meta.XR;
using UnityEngine;
using Stopwatch = System.Diagnostics.Stopwatch;

//Format pachete trimise intre Unity si server:
//
//      [packet_length: 4 bytes, big-endian]
//      [metadata_length: 4 bytes, big-endian]
//      [metadata: JSON codificat UTF-8]
//      [imagine: JPEG]
//
//      packet_length = 4 + metadata + imagine

public class PassthroughTcpSender : MonoBehaviour
{
    [Header("Camera")]
    [SerializeField] private PassthroughCameraAccess cameraAccess;

    [Header("Server")]
    //pentru conexiune wifi
    //[SerializeField] private string serverIp = "192.168.1.100";
    //pentru conexiune USB
    [SerializeField] private string serverIp = "127.0.0.1";
    [SerializeField] private int port = 5000;

    [Header("Streaming")]
    [SerializeField, Range(1, 30)] private int fps = 10;
    [SerializeField, Range(1, 100)] private int jpegQuality = 65;

    private const int MaxFrameBytes = 20_000_000;
    private const int MaxMetadataBytes = 65_536;
    private const int MaxPacketBytes = sizeof(uint) + MaxMetadataBytes + MaxFrameBytes;
    private const int MaxPendingFrames = 20;
    private const double PendingFrameTimeoutSeconds = 10.0;
    private static readonly long PendingFrameTimeoutTicks =
        (long)(Stopwatch.Frequency * PendingFrameTimeoutSeconds);

    [Serializable]
    private class FrameMetadata
    {
        public string type;
        public string frame_id;
        public string capture_timestamp;
        public string camera_id;
        public int width;
        public int height;
    }

    private class PendingFrame
    {
        public string CaptureTimestamp;
        public string CameraId;
        public int Width;
        public int Height;
        public Pose CameraPose;
        public long SentAtStopwatchTicks;
    }

    public sealed class MatchedFrame
    {
        public ulong FrameId { get; }
        public string CaptureTimestamp { get; }
        public string CameraId { get; }
        public int Width { get; }
        public int Height { get; }
        public Pose CameraPose { get; }
        public Texture2D Texture { get; }

        public MatchedFrame(
            ulong frameId,
            string captureTimestamp,
            string cameraId,
            int width,
            int height,
            Pose cameraPose,
            Texture2D texture)
        {
            FrameId = frameId;
            CaptureTimestamp = captureTimestamp;
            CameraId = cameraId;
            Width = width;
            Height = height;
            CameraPose = cameraPose;
            Texture = texture;
        }
    }

    public MatchedFrame ReceivedFrame { get; private set; }
    public Texture2D ReceivedTexture => ReceivedFrame?.Texture;
    public ulong ReceivedFrameId => ReceivedFrame?.FrameId ?? 0;
    public event Action<MatchedFrame> FrameReceived;

    private TcpClient client;
    private NetworkStream stream;
    private Texture2D image;
    private Texture2D receivedTexture;
    private readonly Dictionary<ulong, PendingFrame> pendingFrames = new();
    private readonly List<ulong> expiredFrameIds = new();

    private bool sending;
    private bool destroyed;
    private bool cameraReadyLogged;
    private bool pendingLimitLogged;

    private float nextFrame;
    private float nextWaitingLog;
    private float nextStatsLog;
    private int sentFrames;
    private ulong nextFrameId = 1;

    private async void Start()
    {
        Debug.Log($"[TCP] Sender pornit pe '{gameObject.name}'.");

        if (cameraAccess == null)
        {
            Debug.LogError(
                "[TCP] Camera Access nu este asignat in Inspector.");
            enabled = false;
            return;
        }

        try
        {
            client = new TcpClient { NoDelay = true };

            Debug.Log(
                $"[TCP] Incerc conectarea la {serverIp}:{port}...");

            await client.ConnectAsync(serverIp, port);

            if (destroyed)
                return;

            stream = client.GetStream();
            nextStatsLog = Time.unscaledTime + 5f;

            Debug.Log($"[TCP] Conectat la {serverIp}:{port}.");
            _ = ReceiveFramesAsync(stream);
        }
        catch (Exception e)
        {
            if (!destroyed)
            {
                Debug.LogError(
                    $"[TCP] Conectarea a esuat: {e}");
            }

            CloseConnection();
        }
    }

    private async void Update()
    {
        ExpirePendingFrames();

        if (stream == null || sending || cameraAccess == null)
            return;

        if (!cameraAccess.IsPlaying)
        {
            if (Time.unscaledTime >= nextWaitingLog)
            {
                Debug.Log(
                    "[TCP] Conexiune activa. Astept cadrele camerei...");
                nextWaitingLog = Time.unscaledTime + 5f;
            }

            return;
        }

        if (!cameraReadyLogged)
        {
            var resolution = cameraAccess.CurrentResolution;

            Debug.Log(
                $"[TCP] Camera este pregatita: " +
                $"{resolution.x}x{resolution.y}.");

            cameraReadyLogged = true;
        }

        if (!cameraAccess.IsUpdatedThisFrame ||
            Time.unscaledTime < nextFrame)
            return;

        if (pendingFrames.Count >= MaxPendingFrames)
        {
            if (!pendingLimitLogged)
            {
                Debug.LogWarning(
                    $"[TCP] Limita de {MaxPendingFrames} cadre pending a fost atinsa; omit cadre noi.");
                pendingLimitLogged = true;
            }

            return;
        }
        pendingLimitLogged = false;

        sending = true;
        nextFrame = Time.unscaledTime + 1f / Mathf.Max(1, fps);

        try
        {
            var size = cameraAccess.CurrentResolution;
            DateTime captureTimestamp = cameraAccess.Timestamp;
            Pose cameraPose = cameraAccess.GetCameraPose();
            string cameraId = cameraAccess.CameraPosition.ToString().ToLowerInvariant();

            if (image == null ||
                image.width != size.x ||
                image.height != size.y)
            {
                if (image != null)
                    Destroy(image);

                image = new Texture2D(
                    size.x,
                    size.y,
                    TextureFormat.RGBA32,
                    false);
            }

            // Memoria returnata de GetColors apartine API-ului.
            image.SetPixelData(cameraAccess.GetColors(), 0);
            image.Apply(false);

            byte[] jpg = image.EncodeToJPG(jpegQuality);
            ulong frameId = nextFrameId++;

            var metadata = new FrameMetadata
            {
                type = "frame",
                frame_id = frameId.ToString(CultureInfo.InvariantCulture),
                capture_timestamp = captureTimestamp.ToString("O", CultureInfo.InvariantCulture),
                camera_id = cameraId,
                width = size.x,
                height = size.y
            };
            byte[] metadataBytes = Encoding.UTF8.GetBytes(JsonUtility.ToJson(metadata));

            if (jpg.Length == 0 || jpg.Length > MaxFrameBytes)
                throw new InvalidDataException($"Dimensiune JPEG invalida: {jpg.Length}");
            if (metadataBytes.Length == 0 || metadataBytes.Length > MaxMetadataBytes)
                throw new InvalidDataException($"Dimensiune metadata invalida: {metadataBytes.Length}");

            // Packet: [packet length][metadata length][UTF-8 JSON][JPEG], lengths are big-endian.
            int packetLength = sizeof(uint) + metadataBytes.Length + jpg.Length;
            byte[] header = new byte[sizeof(uint) * 2];
            WriteUInt32BigEndian(header, 0, (uint)packetLength);
            WriteUInt32BigEndian(header, sizeof(uint), (uint)metadataBytes.Length);

            // Register before the first write so a fast response can be matched immediately.
            pendingFrames.Add(frameId, new PendingFrame
            {
                CaptureTimestamp = metadata.capture_timestamp,
                CameraId = cameraId,
                Width = size.x,
                Height = size.y,
                CameraPose = cameraPose,
                SentAtStopwatchTicks = Stopwatch.GetTimestamp()
            });

            NetworkStream output = stream;

            await output.WriteAsync(header, 0, header.Length);
            await output.WriteAsync(metadataBytes, 0, metadataBytes.Length);
            await output.WriteAsync(jpg, 0, jpg.Length);

            if (destroyed)
                return;

            sentFrames++;

            if (sentFrames == 1)
            {
                Debug.Log(
                    $"[TCP] Primul cadru trimis: ID {frameId}, {jpg.Length} bytes.");
            }

            if (Time.unscaledTime >= nextStatsLog)
            {
                Debug.Log(
                    $"[TCP] Total cadre trimise: {sentFrames}. " +
                    $"Ultimul JPEG: {jpg.Length} bytes.");

                nextStatsLog = Time.unscaledTime + 5f;
            }
        }
        catch (Exception e)
        {
            if (!destroyed)
                Debug.LogError($"[TCP] Trimiterea a esuat: {e}");

            CloseConnection();
        }
        finally
        {
            sending = false;
        }
    }

    private static async Task ReadExactAsync(NetworkStream input, byte[] buffer)
    {
        int offset = 0;
        while (offset < buffer.Length)
        {
            int count = await input.ReadAsync(buffer, offset, buffer.Length - offset);
            if (count == 0)
                throw new EndOfStreamException("Serverul a inchis conexiunea.");
            offset += count;
        }
    }

    private async Task ReceiveFramesAsync(NetworkStream input)
    {
        bool firstFrame = true;
        var packetLengthHeader = new byte[sizeof(uint)];
        var metadataLengthHeader = new byte[sizeof(uint)];

        try
        {
            while (!destroyed)
            {
                await ReadExactAsync(input, packetLengthHeader);
                uint packetLength = ReadUInt32BigEndian(packetLengthHeader, 0);
                if (packetLength < sizeof(uint) + 1 || packetLength > MaxPacketBytes)
                    throw new InvalidDataException($"Lungime pachet invalida: {packetLength}");

                await ReadExactAsync(input, metadataLengthHeader);
                uint metadataLength = ReadUInt32BigEndian(metadataLengthHeader, 0);
                if (metadataLength == 0 || metadataLength > MaxMetadataBytes ||
                    metadataLength > packetLength - sizeof(uint))
                    throw new InvalidDataException($"Lungime metadata invalida: {metadataLength}");

                uint imageLength = packetLength - sizeof(uint) - metadataLength;
                if (imageLength == 0 || imageLength > MaxFrameBytes)
                    throw new InvalidDataException($"Lungime JPEG invalida: {imageLength}");

                var metadataBytes = new byte[(int)metadataLength];
                await ReadExactAsync(input, metadataBytes);
                string metadataJson = new UTF8Encoding(false, true).GetString(metadataBytes);
                FrameMetadata metadata = JsonUtility.FromJson<FrameMetadata>(metadataJson);
                if (metadata == null || metadata.type != "processing_result" ||
                    string.IsNullOrEmpty(metadata.capture_timestamp) ||
                    string.IsNullOrEmpty(metadata.camera_id) || metadata.width <= 0 || metadata.height <= 0 ||
                    !ulong.TryParse(metadata.frame_id, NumberStyles.None, CultureInfo.InvariantCulture, out ulong frameId))
                    throw new InvalidDataException("Metadata rezultat invalida.");

                var jpeg = new byte[(int)imageLength];
                await ReadExactAsync(input, jpeg);
                if (destroyed)
                    return;

                ExpirePendingFrames();

                if (!pendingFrames.TryGetValue(frameId, out PendingFrame pendingFrame))
                {
                    Debug.LogWarning($"[TCP] Rezultat fara cadru pending: ID {frameId}.");
                    continue;
                }

                pendingFrames.Remove(frameId);
                if (!string.Equals(
                        metadata.frame_id,
                        frameId.ToString(CultureInfo.InvariantCulture),
                        StringComparison.Ordinal) ||
                    !string.Equals(
                        pendingFrame.CaptureTimestamp,
                        metadata.capture_timestamp,
                        StringComparison.Ordinal) ||
                    !string.Equals(pendingFrame.CameraId, metadata.camera_id, StringComparison.Ordinal) ||
                    pendingFrame.Width != metadata.width || pendingFrame.Height != metadata.height)
                {
                    Debug.LogError($"[TCP] Contextul raspunsului nu corespunde cadrului {frameId}.");
                    continue;
                }

                pendingLimitLogged = false;

                // Dupa await, executia continua pe firul principal Unity, unde putem modifica texturile.
                if (receivedTexture == null)
                    receivedTexture = new Texture2D(2, 2, TextureFormat.RGB24, false);

                if (!receivedTexture.LoadImage(jpeg))
                    throw new InvalidDataException("JPEG primit invalid.");
                if (receivedTexture.width != metadata.width || receivedTexture.height != metadata.height)
                    throw new InvalidDataException("Dimensiunile JPEG nu corespund metadata-ului.");

                ReceivedFrame = new MatchedFrame(
                    frameId,
                    pendingFrame.CaptureTimestamp,
                    pendingFrame.CameraId,
                    pendingFrame.Width,
                    pendingFrame.Height,
                    pendingFrame.CameraPose,
                    receivedTexture);
                FrameReceived?.Invoke(ReceivedFrame);

                if (firstFrame)
                {
                    Debug.Log($"[TCP] Primul rezultat primit pentru cadrul {frameId}: {imageLength} bytes.");
                    firstFrame = false;
                }
            }
        }
        catch (Exception e)
        {
            if (!destroyed)
                Debug.LogError($"[TCP] Receptia a esuat: {e}");
            CloseConnection();
        }
    }

    private void CloseConnection()
    {
        stream = null;
        client?.Close();
        client = null;
        pendingFrames.Clear();
        pendingLimitLogged = false;
    }

    private void ExpirePendingFrames()
    {
        if (pendingFrames.Count == 0)
            return;

        long now = Stopwatch.GetTimestamp();
        expiredFrameIds.Clear();
        foreach (KeyValuePair<ulong, PendingFrame> entry in pendingFrames)
        {
            if (now - entry.Value.SentAtStopwatchTicks >= PendingFrameTimeoutTicks)
                expiredFrameIds.Add(entry.Key);
        }

        foreach (ulong frameId in expiredFrameIds)
            pendingFrames.Remove(frameId);

        if (expiredFrameIds.Count > 0)
        {
            Debug.LogWarning($"[TCP] Au expirat {expiredFrameIds.Count} raspunsuri pending.");
            pendingLimitLogged = false;
        }
    }

    private static uint ReadUInt32BigEndian(byte[] data, int offset)
    {
        return ((uint)data[offset] << 24) |
               ((uint)data[offset + 1] << 16) |
               ((uint)data[offset + 2] << 8) |
               data[offset + 3];
    }

    private static void WriteUInt32BigEndian(byte[] data, int offset, uint value)
    {
        data[offset] = (byte)(value >> 24);
        data[offset + 1] = (byte)(value >> 16);
        data[offset + 2] = (byte)(value >> 8);
        data[offset + 3] = (byte)value;
    }

    private void OnDestroy()
    {
        destroyed = true;
        CloseConnection();

        if (image != null)
            Destroy(image);

        if (receivedTexture != null)
            Destroy(receivedTexture);
    }
}
