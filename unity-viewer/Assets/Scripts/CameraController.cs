using UnityEngine;

namespace Edificio.Viewer
{
    [RequireComponent(typeof(Camera))]
    public class CameraController : MonoBehaviour
    {
        public Transform target;
        public Vector3 targetOffset = Vector3.zero;
        public float distance = 120f;
        public float minDistance = 5f;
        public float maxDistance = 400f;
        public float rotSpeed = 0.25f;
        public float zoomSpeed = 1.2f;

        float _yaw = 30f;
        float _pitch = 25f;

        public void LookAt(Vector3 center, float radius)
        {
            targetOffset = center;
            distance = Mathf.Clamp(radius * 1.8f, minDistance, maxDistance);
            _pitch = 28f;
            _yaw = 35f;
            Apply();
        }

        void Update()
        {
            if (Input.GetMouseButton(1))
            {
                _yaw += Input.GetAxis("Mouse X") * rotSpeed * 100f;
                _pitch -= Input.GetAxis("Mouse Y") * rotSpeed * 100f;
                _pitch = Mathf.Clamp(_pitch, 5f, 85f);
            }

            float scroll = Input.GetAxis("Mouse ScrollWheel");
            if (Mathf.Abs(scroll) > 0.0001f)
                distance = Mathf.Clamp(distance * (1f - scroll * zoomSpeed), minDistance, maxDistance);

            if (Input.GetMouseButton(2))
            {
                float sx = Input.GetAxis("Mouse X");
                float sy = Input.GetAxis("Mouse Y");
                var fwd = Quaternion.Euler(_pitch, _yaw, 0) * Vector3.forward;
                var right = Quaternion.Euler(0, _yaw, 0) * Vector3.right;
                targetOffset += (right * -sx + Vector3.up * sy) * distance * 0.0012f;
            }

            Apply();
        }

        void Apply()
        {
            var q = Quaternion.Euler(_pitch, _yaw, 0);
            var dir = q * Vector3.forward;
            transform.position = targetOffset - dir * distance;
            transform.rotation = q;
        }

        void LateUpdate()
        {
            if (target != null) targetOffset = target.position;
        }
    }
}