using System.Collections.Generic;
using PassthroughCameraSamples.CameraViewer;
using UnityEngine;
using UnityEngine.UI;

/// <summary>
/// Draws server translations over the local camera image. The server's polygons
/// are frame-relative, so overlays are invalidated after significant headset motion.
/// </summary>
public sealed class TextRegionOverlayRenderer : MonoBehaviour
{
    [SerializeField, Min(0f)] private float maxCameraTranslationMeters = 0.05f;
    [SerializeField, Range(0f, 45f)] private float maxCameraRotationDegrees = 5f;

    private sealed class OverlayEntry
    {
        public RectTransform Rect;
        public Text Label;
    }

    private readonly Dictionary<string, OverlayEntry> overlays = new();
    private RectTransform overlayRoot;
    private Pose sourcePose;
    private bool hasSourcePose;
    private bool invalidatedByMotion;
    private ulong latestFrameId;

    private void Awake()
    {
        overlayRoot = transform as RectTransform;
    }

    public void ApplyFrame(PassthroughTcpSender.MatchedFrame frame)
    {
        if (frame == null || frame.FrameId < latestFrameId || overlayRoot == null)
            return;

        latestFrameId = frame.FrameId;
        sourcePose = frame.CameraPose;
        hasSourcePose = true;
        invalidatedByMotion = false;

        var present = new HashSet<string>();
        foreach (PassthroughTcpSender.RegionMetadata region in frame.Regions)
        {
            if (region == null || string.IsNullOrEmpty(region.region_id) ||
                string.IsNullOrWhiteSpace(region.translation) ||
                region.polygon == null || region.polygon.Length < 4)
                continue;

            present.Add(region.region_id);
            OverlayEntry entry = GetOrCreate(region.region_id);
            entry.Label.text = region.translation;
            Position(entry.Rect, region.polygon, frame.Width, frame.Height);
        }

        var staleIds = new List<string>();
        foreach (string regionId in overlays.Keys)
        {
            if (!present.Contains(regionId))
                staleIds.Add(regionId);
        }

        foreach (string regionId in staleIds)
            Remove(regionId);
    }

    public void UpdateCameraPose(Pose cameraPose)
    {
        if (!hasSourcePose || invalidatedByMotion)
            return;

        float translation = Vector3.Distance(sourcePose.position, cameraPose.position);
        float rotation = Quaternion.Angle(sourcePose.rotation, cameraPose.rotation);
        if (translation <= maxCameraTranslationMeters && rotation <= maxCameraRotationDegrees)
            return;

        ClearOverlays();
        invalidatedByMotion = true;
    }

    public void ClearOverlays()
    {
        foreach (OverlayEntry entry in overlays.Values)
        {
            if (entry.Rect != null)
                Destroy(entry.Rect.gameObject);
        }

        overlays.Clear();
    }

    private OverlayEntry GetOrCreate(string regionId)
    {
        if (overlays.TryGetValue(regionId, out OverlayEntry existing))
            return existing;

        var rootObject = new GameObject(
            $"Translation_{regionId}",
            typeof(RectTransform),
            typeof(CanvasRenderer),
            typeof(Image));
        rootObject.transform.SetParent(overlayRoot, false);
        var rootRect = (RectTransform)rootObject.transform;
        rootRect.anchorMin = new Vector2(0.5f, 0.5f);
        rootRect.anchorMax = new Vector2(0.5f, 0.5f);
        rootRect.pivot = new Vector2(0.5f, 0.5f);

        var background = rootObject.GetComponent<Image>();
        background.color = new Color(0f, 0f, 0f, 0.78f);
        background.raycastTarget = false;

        var labelObject = new GameObject(
            "Label",
            typeof(RectTransform),
            typeof(CanvasRenderer),
            typeof(Text));
        labelObject.transform.SetParent(rootObject.transform, false);
        var labelRect = (RectTransform)labelObject.transform;
        labelRect.anchorMin = Vector2.zero;
        labelRect.anchorMax = Vector2.one;
        labelRect.offsetMin = new Vector2(4f, 2f);
        labelRect.offsetMax = new Vector2(-4f, -2f);

        var label = labelObject.GetComponent<Text>();
        label.font = Resources.GetBuiltinResource<Font>("Arial.ttf");
        label.color = Color.white;
        label.alignment = TextAnchor.MiddleCenter;
        label.resizeTextForBestFit = true;
        label.resizeTextMinSize = 8;
        label.resizeTextMaxSize = 48;
        label.horizontalOverflow = HorizontalWrapMode.Wrap;
        label.verticalOverflow = VerticalWrapMode.Truncate;
        label.raycastTarget = false;

        var created = new OverlayEntry
        {
            Rect = rootRect,
            Label = label
        };
        overlays.Add(regionId, created);
        return created;
    }

    private void Position(RectTransform rect, PassthroughTcpSender.RegionPoint[] polygon, int imageWidth, int imageHeight)
    {
        if (imageWidth <= 0 || imageHeight <= 0)
        {
            rect.gameObject.SetActive(false);
            return;
        }

        float minX = float.MaxValue;
        float maxX = float.MinValue;
        float minY = float.MaxValue;
        float maxY = float.MinValue;
        foreach (PassthroughTcpSender.RegionPoint point in polygon)
        {
            if (point == null)
                continue;
            minX = Mathf.Min(minX, point.x);
            maxX = Mathf.Max(maxX, point.x);
            minY = Mathf.Min(minY, point.y);
            maxY = Mathf.Max(maxY, point.y);
        }

        if (minX == float.MaxValue)
        {
            rect.gameObject.SetActive(false);
            return;
        }

        float scaleX = overlayRoot.rect.width / imageWidth;
        float scaleY = overlayRoot.rect.height / imageHeight;
        float centerX = (minX + maxX) * 0.5f * scaleX - overlayRoot.rect.width * 0.5f;
        float centerY = overlayRoot.rect.height * 0.5f - (minY + maxY) * 0.5f * scaleY;

        rect.anchoredPosition = new Vector2(centerX, centerY);
        rect.sizeDelta = new Vector2(
            Mathf.Max(24f, (maxX - minX) * scaleX),
            Mathf.Max(18f, (maxY - minY) * scaleY));
        rect.gameObject.SetActive(true);
    }

    private void Remove(string regionId)
    {
        if (!overlays.TryGetValue(regionId, out OverlayEntry entry))
            return;
        overlays.Remove(regionId);
        if (entry.Rect != null)
            Destroy(entry.Rect.gameObject);
    }

    private void OnDestroy() => ClearOverlays();
}
