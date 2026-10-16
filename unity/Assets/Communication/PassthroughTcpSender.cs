using System;
using System.Net.Sockets;
using Meta.XR;
using UnityEngine;

public class PassthroughTcpSender : MonoBehaviour
{
    [Header("Camera")]
    [SerializeField] private PassthroughCameraAccess cameraAccess;

    [Header("Server")]
    [SerializeField] private string serverIp = "192.168.1.100";
    [SerializeField] private int port = 5000;

    [Header("Streaming")]
    [SerializeField, Range(1, 30)] private int fps = 10;
    [SerializeField, Range(1, 100)] private int jpegQuality = 65;

    private TcpClient client;
    private NetworkStream stream;
    private Texture2D image;

    private bool sending;
    private bool destroyed;
    private bool cameraReadyLogged;

    private float nextFrame;
    private float nextWaitingLog;
    private float nextStatsLog;
    private int sentFrames;

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

        sending = true;
        nextFrame = Time.unscaledTime + 1f / Mathf.Max(1, fps);

        try
        {
            var size = cameraAccess.CurrentResolution;

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

            // Protocol: [4 bytes lungime, big-endian][JPEG]
            // (facem manual conversia).
            int length = jpg.Length;
            byte[] header =
            {
                (byte)(length >> 24),
                (byte)(length >> 16),
                (byte)(length >> 8),
                (byte)length
            };

            NetworkStream output = stream;

            await output.WriteAsync(header, 0, header.Length);
            await output.WriteAsync(jpg, 0, jpg.Length);

            if (destroyed)
                return;

            sentFrames++;

            if (sentFrames == 1)
            {
                Debug.Log(
                    $"[TCP] Primul cadru trimis: {length} bytes.");
            }

            if (Time.unscaledTime >= nextStatsLog)
            {
                Debug.Log(
                    $"[TCP] Total cadre trimise: {sentFrames}. " +
                    $"Ultimul JPEG: {length} bytes.");

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

    private void CloseConnection()
    {
        stream = null;
        client?.Close();
        client = null;
    }

    private void OnDestroy()
    {
        destroyed = true;
        CloseConnection();

        if (image != null)
            Destroy(image);
    }
}
