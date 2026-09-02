using System.Collections.Generic;
using UnityEngine;
using UnityEngine.EventSystems;

namespace Edificio.Viewer
{
    public class MainViewer : MonoBehaviour
    {
        [Header("Geometria visual")]
        public float columnaRadio = 0.45f;
        public float vigaRadio = 0.40f;
        public float diagonalRadio = 0.12f;
        public bool mostrarNodos = true;
        public bool mostrarApoyos = true;
        public bool mostrarGrilla = true;

        Camera _cam;
        CameraController _camCtrl;
        InfoPanel _panel;
        GameObject _modelo;
        Vector3 _center;
        float _radius;
        bool _built;
        readonly List<ElementItem> _items = new List<ElementItem>();

        void Start()
        {
            EnsureCamera();
            EnsurePanel();
            if (_built)
            {
                _camCtrl.LookAt(_center, _radius);
            }
            else
            {
                Build();
            }
        }

        public void BuildEditMode()
        {
            ClearModel();
            Build();
            _built = true;
            FrameCameraEdit();
        }

        void ClearModel()
        {
            if (_modelo != null)
            {
                if (Application.isPlaying) Destroy(_modelo);
                else DestroyImmediate(_modelo);
                _modelo = null;
            }
            _items.Clear();
        }

        void FrameCameraEdit()
        {
            var nodos = BuildingLoader.LoadNodos();
            if (nodos.Count == 0 || Camera.main == null) return;
            var center = ComputeCenter(nodos);
            var dist = ComputeRadius(nodos, center) * 1.8f;
            var cam = Camera.main.transform;
            cam.position = center - new Vector3(dist * 0.45f, -dist * 0.55f, dist) ;
            cam.rotation = Quaternion.LookRotation(center - cam.position, Vector3.up);
        }

        void EnsureCamera()
        {
            if (Camera.main != null)
            {
                _cam = Camera.main;
                _camCtrl = _cam.GetComponent<CameraController>();
                if (_camCtrl == null) _camCtrl = _cam.gameObject.AddComponent<CameraController>();
                return;
            }

            var go = new GameObject("Main Camera");
            go.tag = "MainCamera";
            _cam = go.AddComponent<Camera>();
            _cam.backgroundColor = new Color(0.13f, 0.15f, 0.17f);
            _cam.clearFlags = CameraClearFlags.SolidColor;
            _cam.farClipPlane = 2000f;
            go.AddComponent<AudioListener>();
            _camCtrl = go.AddComponent<CameraController>();
        }

        void EnsurePanel()
        {
            var found = FindObjectOfType<InfoPanel>();
            _panel = found != null
                ? found
                : new GameObject("Viewer UI").AddComponent<InfoPanel>();
        }

        public void Rebuild()
        {
            ClearModel();
            Build();
        }

        public void Build()
        {
            var nodos = BuildingLoader.LoadNodos();
            var grilla = BuildingLoader.LoadGrilla();
            var elementos = BuildingLoader.LoadElementos();
            var trib = BuildingLoader.LoadTributarias();
            var apoyos = BuildingLoader.LoadApoyos();

            _modelo = new GameObject("Modelo");
            _modelo.transform.SetParent(transform, false);

            // Grilla de pisos (planos translucidos)
            if (mostrarGrilla && grilla != null)
                BuildGrilla(grilla);

            foreach (var el in elementos)
            {
                TributariaViga t = null;
                if (el.elementTag.HasValue && trib.ContainsKey(el.elementTag.Value))
                    t = trib[el.elementTag.Value];
                BuildElemento(el, nodos, t, grilla);
            }

            if (mostrarNodos) BuildNodos(nodos);
            if (mostrarApoyos) BuildApoyos(apoyos, nodos);

            if (nodos.Count > 0)
            {
                _center = ComputeCenter(nodos);
                _radius = ComputeRadius(nodos, _center);
                if (_camCtrl != null) _camCtrl.LookAt(_center, _radius);
            }
        }

        void BuildElemento(ElementoJson el, Dictionary<int, Vector3> nodos, TributariaViga t, GrillaFile grilla)
        {
            GameObject go;
            TipoColor color;

            switch (el.tipo)
            {
                case "columna":
                    go = MakeBar(nodos[el.n1.Value], nodos[el.n2.Value], columnaRadio);
                    color = TipoColor.Columna;
                    break;
                case "diagonal":
                    go = MakeBar(nodos[el.n1.Value], nodos[el.n2.Value], diagonalRadio);
                    color = TipoColor.Diagonal;
                    break;
                case "viga":
                    go = MakeBar(nodos[el.n1.Value], nodos[el.n2.Value], vigaRadio);
                    color = el.esVoladizo == true ? TipoColor.Voladizo : TipoColor.Viga;
                    break;
                case "muro":
                    go = MakeMuro(el, grilla);
                    if (go == null) return;
                    color = TipoColor.Muro;
                    break;
                default:
                    return;
            }

            var renderer = go.GetComponent<Renderer>();
            renderer.sharedMaterial = MakeMat(BuildingColors.Get(color));

            var item = go.AddComponent<ElementItem>();
            item.Setup(el, t);
            _items.Add(item);

            go.name = item.etiqueta;
        }

        GameObject MakeBar(Vector3 a, Vector3 b, float radio)
        {
            var cube = GameObject.CreatePrimitive(PrimitiveType.Cube);
            cube.transform.SetParent(_modelo.transform, false);
            cube.transform.position = (a + b) * 0.5f;
            var dir = b - a;
            cube.transform.rotation = Quaternion.FromToRotation(Vector3.up, dir);
            cube.transform.localScale = new Vector3(radio * 2f, dir.magnitude, radio * 2f);
            return cube;
        }

        GameObject MakeMuro(ElementoJson el, GrillaFile grilla)
        {
            if (grilla == null) return null;

            float elev0 = grilla.niveles.ContainsKey("base") ? grilla.niveles["base"] : 0f;
            float zA = GetValor(grilla, el.desdeNivel, "nivel");
            float zB = GetValor(grilla, el.hastaNivel, "nivel");
            float yMin = Mathf.Min(zA, zB, elev0);
            float yMax = Mathf.Max(zA, zB);
            float h = Mathf.Max(yMax - yMin, 0.1f);

            float t = el.espesor ?? 0.2f;

            Vector3 pos;
            Vector3 scale;
            if (el.orientacion == "Y")
            {
                // muro paralelo al eje Y (Unity Z), en X = linea_eje
                float z0 = GetValor(grilla, el.desdeEje, "y");
                float z1 = GetValor(grilla, el.hastaEje, "y");
                float w = Mathf.Max(Mathf.Abs(z1 - z0), 0.1f);
                float zMid = (z0 + z1) * 0.5f;
                pos = new Vector3(GetValor(grilla, el.lineaEje, "x"), (yMin + yMax) * 0.5f, zMid);
                scale = new Vector3(t, h, w);
            }
            else if (el.orientacion == "X")
            {
                // muro paralelo al eje X (Unity X), en Y = linea_eje
                float x0 = GetValor(grilla, el.desdeEje, "x");
                float x1 = GetValor(grilla, el.hastaEje, "x");
                float w = Mathf.Max(Mathf.Abs(x1 - x0), 0.1f);
                float xMid = (x0 + x1) * 0.5f;
                pos = new Vector3(xMid, (yMin + yMax) * 0.5f, GetValor(grilla, el.lineaEje, "y"));
                scale = new Vector3(w, h, t);
            }
            else return null;

            var cube = GameObject.CreatePrimitive(PrimitiveType.Cube);
            cube.transform.SetParent(_modelo.transform, false);
            cube.transform.position = pos;
            cube.transform.localScale = scale;

            var mat = MakeMat(BuildingColors.Get(TipoColor.Muro));
            cube.GetComponent<Renderer>().sharedMaterial = mat;
            return cube;
        }

        static Material MakeMat(Color c)
        {
            var sh = Shader.Find("Standard");
            var m = new Material(sh != null ? sh : Shader.Find("Diffuse"));
            m.color = c;
            return m;
        }

        static float GetValor(GrillaFile g, string name, string tipo)
        {
            switch (tipo)
            {
                case "x": return g.ejesX.ContainsKey(name) ? g.ejesX[name] : 0f;
                case "y": return g.ejesY.ContainsKey(name) ? g.ejesY[name] : 0f;
                case "nivel": return g.niveles.ContainsKey(name) ? g.niveles[name] : 0f;
                default: return 0f;
            }
        }

        void BuildGrilla(GrillaFile g)
        {
            float zMin = 0f;
            float zMax = 0f;
            foreach (var kv in g.niveles)
            {
                zMin = Mathf.Min(zMin, kv.Value);
                zMax = Mathf.Max(zMax, kv.Value);
            }

            foreach (var kv in g.niveles)
            {
                var plane = GameObject.CreatePrimitive(PrimitiveType.Cube);
                plane.transform.SetParent(_modelo.transform, false);
                float spanX = 0f, spanz = 0f;
                foreach (var x in g.ejesX.Values) spanX = Mathf.Max(spanX, x);
                foreach (var y in g.ejesY.Values) spanz = Mathf.Max(spanz, y);
                plane.transform.localScale = new Vector3(spanX + 4f, 0.05f, spanz + 4f);
                plane.transform.position = new Vector3(spanX * 0.5f, kv.Value + 0.001f, spanz * 0.5f);

                var mat = MakeMat(new Color(1f, 1f, 1f, 0.05f));
                plane.GetComponent<Renderer>().sharedMaterial = mat;
            }
        }

        void BuildNodos(Dictionary<int, Vector3> nodos)
        {
            foreach (var kv in nodos)
            {
                var s = GameObject.CreatePrimitive(PrimitiveType.Sphere);
                s.transform.SetParent(_modelo.transform, false);
                s.transform.position = kv.Value;
                s.transform.localScale = Vector3.one * 0.35f;
                s.GetComponent<Renderer>().sharedMaterial = MakeMat(BuildingColors.Get(TipoColor.Nodo));
            }
        }

        void BuildApoyos(List<ApoyoJson> apoyos, Dictionary<int, Vector3> nodos)
        {
            foreach (var a in apoyos)
            {
                if (!nodos.ContainsKey(a.tag)) continue;
                var s = GameObject.CreatePrimitive(PrimitiveType.Sphere);
                s.transform.SetParent(_modelo.transform, false);
                var p = nodos[a.tag];
                p.y -= 0.25f;
                s.transform.position = p;
                s.transform.localScale = Vector3.one * 1.1f;
                s.GetComponent<Renderer>().sharedMaterial = MakeMat(BuildingColors.Get(TipoColor.Apoyo));
            }
        }

        static Vector3 ComputeCenter(Dictionary<int, Vector3> nodos)
        {
            var acc = Vector3.zero;
            foreach (var kv in nodos) acc += kv.Value;
            return acc / nodos.Count;
        }

        static float ComputeRadius(Dictionary<int, Vector3> nodos, Vector3 center)
        {
            float r = 0f;
            foreach (var kv in nodos)
                r = Mathf.Max(r, Vector3.Distance(kv.Value, center));
            return Mathf.Max(r, 1f);
        }

        void Update()
        {
            if (_cam == null) return;
            if (Input.GetMouseButtonDown(0) && Input.GetKey(KeyCode.LeftAlt) == false)
            {
                if (EventSystem.current != null && EventSystem.current.IsPointerOverGameObject())
                    return;

                var ray = _cam.ScreenPointToRay(Input.mousePosition);
                if (Physics.Raycast(ray, out var hit, 2000f))
                {
                    var item = hit.collider.GetComponentInParent<ElementItem>();
                    if (item != null) { _panel.Select(item); return; }
                }
                _panel.Deselect();
            }
        }
    }
}