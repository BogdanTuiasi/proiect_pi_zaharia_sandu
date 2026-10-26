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

        private PassthroughTcpSender m_tcpSender;
        private bool m_showingReceivedFrame;
        private bool m_hasDisplayedFrameId;
        private ulong m_lastDisplayedFrameId;

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
            m_image.texture = frame.Texture;
            m_showingReceivedFrame = true;
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
            // Afisam camera locala pana la primirea primului cadru procesat.
            if (!m_showingReceivedFrame)
                m_image.texture = m_cameraAccess.GetTexture();
        }

        private void Update() => m_debugText.text = OVRPermissionsRequester.IsPermissionGranted(OVRPermissionsRequester.Permission.PassthroughCameraAccess) ? "Permission granted." : "No permission granted.";
    }
}
