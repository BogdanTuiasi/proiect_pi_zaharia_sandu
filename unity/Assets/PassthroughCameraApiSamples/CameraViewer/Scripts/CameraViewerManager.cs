// Copyright (c) Meta Platforms, Inc. and affiliates.

using System.Collections;
using Meta.XR;
using Meta.XR.Samples;
using UnityEngine;
using UnityEngine.Assertions;
using UnityEngine.UI;

namespace PassthroughCameraSamples.CameraViewer
{
    [MetaCodeSample("PassthroughCameraApiSamples-CameraViewer")]
    public class CameraViewerManager : MonoBehaviour
    {
        [SerializeField] private PassthroughCameraAccess m_cameraAccess;
        [SerializeField] private Text m_debugText;
        [SerializeField] private RawImage m_image;
        [SerializeField] private TextRegionOverlayRenderer m_overlayRenderer;

        private PassthroughTcpSender m_tcpSender;
        private bool m_hasDisplayedFrameId;
        private ulong m_lastDisplayedFrameId;
        private int m_lastLoggedUnityFrameCount;
        private int m_lastLoggedSentFrameCount;
        private float m_statsWindowStart;

        private void OnEnable()
        {
            // Senderul este atasat obiectului cu acces la camera din CameraViewer.
            m_tcpSender = m_cameraAccess.GetComponent<PassthroughTcpSender>();
            if (m_tcpSender == null)
            {
                Debug.LogWarning("[TCP] Sender lipsa pe obiectul Camera Access.");
                return;
            }

            m_tcpSender.FrameReceived += ShowReceivedFrame;
            m_lastLoggedSentFrameCount = m_tcpSender.SentFrameCount;
            m_lastLoggedUnityFrameCount = Time.frameCount;
            m_statsWindowStart = Time.unscaledTime;
            if (m_tcpSender.ReceivedFrame != null)
                ShowReceivedFrame(m_tcpSender.ReceivedFrame);
        }

        private void OnDisable()
        {
            if (m_tcpSender != null)
                m_tcpSender.FrameReceived -= ShowReceivedFrame;
        }

        private void ShowReceivedFrame(PassthroughTcpSender.MatchedFrame frame)
        {
            if (m_hasDisplayedFrameId && frame.FrameId <= m_lastDisplayedFrameId)
            {
                Debug.Log($"[TCP] Ignor rezultat vechi pentru cadrul {frame.FrameId}.");
                return;
            }

            m_hasDisplayedFrameId = true;
            m_lastDisplayedFrameId = frame.FrameId;
            m_overlayRenderer?.ApplyFrame(frame);
        }

        private IEnumerator Start()
        {
            var supportedResolutions = PassthroughCameraAccess.GetSupportedResolutions(PassthroughCameraAccess.CameraPositionType.Left);
            Assert.IsNotNull(supportedResolutions, nameof(supportedResolutions));
            Debug.Log($"PassthroughCameraAccess.GetSupportedResolutions(): {string.Join(", ", supportedResolutions)}");

            while (!m_cameraAccess.IsPlaying)
            {
                yield return null;
            }
            // Pastreaza RawImage legat de textura locala, actualizata de API-ul camerei.
            m_image.texture = m_cameraAccess.GetTexture();
        }

        private void Update()
        {
            m_debugText.text = OVRPermissionsRequester.IsPermissionGranted(OVRPermissionsRequester.Permission.PassthroughCameraAccess)
                ? "Permission granted."
                : "No permission granted.";

            if (m_cameraAccess != null && m_cameraAccess.IsPlaying)
                m_overlayRenderer?.UpdateCameraPose(m_cameraAccess.GetCameraPose());

            if (m_tcpSender == null)
                return;

            float now = Time.unscaledTime;
            float elapsed = now - m_statsWindowStart;
            if (elapsed < 1f)
                return;

            int sentTotal = m_tcpSender.SentFrameCount;
            int sentInWindow = sentTotal - m_lastLoggedSentFrameCount;
            int unityFramesInWindow = Time.frameCount - m_lastLoggedUnityFrameCount;
            Debug.Log(
                $"[FPS] Trimise catre server: {sentInWindow / elapsed:F1} cadre/s " +
                $"(total {sentTotal}); cadre Unity: {unityFramesInWindow / elapsed:F1} cadre/s.");

            m_lastLoggedSentFrameCount = sentTotal;
            m_lastLoggedUnityFrameCount = Time.frameCount;
            m_statsWindowStart = now;
        }
    }
}
