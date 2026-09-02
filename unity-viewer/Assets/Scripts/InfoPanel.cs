using UnityEngine;
using UnityEngine.UI;

namespace Edificio.Viewer
{
    public class InfoPanel : MonoBehaviour
    {
        public static InfoPanel Instance { get; private set; }

        Text _titulo;
        Text _texto;
        ElementItem _actual;
        Color _prevColor;

        void Awake()
        {
            Instance = this;
            BuildUI();
        }

        public void Select(ElementItem item)
        {
            if (_actual != null && _actual != item)
                _actual.SetSelected(false);

            _actual = item;
            item.SetSelected(true);

            _titulo.text = item.etiqueta;
            _texto.text = Format(item);
        }

        public void Deselect()
        {
            if (_actual == null) return;
            _actual.SetSelected(false);
            _actual = null;
            _titulo.text = "";
            _texto.text = "";
        }

        public bool HasSelection => _actual != null;

        static string Format(ElementItem i)
        {
            var e = i.element;
            var sb = new System.Text.StringBuilder();

            string tipo = e.tipo;
            if (e.esVoladizo == true) tipo += " (voladizo)";
            sb.AppendLine($"Tipo        : {tipo}");

            if (e.elementTag.HasValue) sb.AppendLine($"Element tag : {e.elementTag}");

            if (e.tipo == "muro")
            {
                sb.AppendLine($"Muro        : {e.nombre}");
                sb.AppendLine($"Orientacion : {e.orientacion} - {e.lineaEje}");
                sb.AppendLine($"Extiende    : {e.desdeEje} a {e.hastaEje}");
                sb.AppendLine($"Niveles     : {e.desdeNivel} a {e.hastaNivel}");
            }
            else
            {
                sb.AppendLine($"Nivel       : {e.nivel}");
                if (e.esVoladizo == true)
                {
                    sb.AppendLine($"Voladizo    : {e.desdeEje} ({e.ejeY}) hacia {e.hastaEje}");
                }
                else if (e.orientacion != null)
                {
                    sb.AppendLine($"Orientacion : {e.orientacion}");
                    sb.AppendLine($"Grilla      : ix={e.ix}, iy={e.iy}, k={e.k}");
                }
            }

            sb.AppendLine($"Seccion     : {e.seccion}");
            sb.AppendLine($"Material    : {e.material}");

            if (e.L.HasValue)
            {
                sb.AppendLine(string.Format("L           : {0:F3} m", e.L.Value));
            }

            if (i.trib != null)
            {
                sb.AppendLine(string.Format("w losa      : {0:F3} kN/m", i.trib.wKNm));
                sb.AppendLine(string.Format("carga losa  : {0:F3} kN", i.trib.cargaLosa));
            }

            return sb.ToString().TrimEnd();
        }

        void BuildUI()
        {
            var canvasGO = new GameObject("InfoCanvas");
            canvasGO.transform.SetParent(transform, false);
            var canvas = canvasGO.AddComponent<Canvas>();
            canvas.renderMode = RenderMode.ScreenSpaceOverlay;
            canvasGO.AddComponent<CanvasScaler>().uiScaleMode =
                CanvasScaler.ScaleMode.ScaleWithScreenSize;
            canvasGO.AddComponent<GraphicRaycaster>();
            canvasGO.AddComponent<CanvasGroup>().blocksRaycasts = true;

            var font = Resources.GetBuiltinResource<Font>("LegacyRuntime.ttf");
            if (font == null) font = Resources.GetBuiltinResource<Font>("Arial.ttf");

            var bg = NewRect(canvasGO.transform, "Bg",
                new Vector2(0, 1), new Vector2(0, 1), new Vector2(10, -10), new Vector2(340, 420));
            var img = bg.gameObject.AddComponent<Image>();
            img.color = new Color(0f, 0f, 0f, 0.72f);

            _titulo = NewText(bg.transform, "Titulo",
                new Vector2(0, 1), new Vector2(0, 1), new Vector2(12, -8), new Vector2(316, 24),
                font, 16, FontStyle.Bold, Color.white);

            _texto = NewText(bg.transform, "Texto",
                new Vector2(0, 1), new Vector2(0, 1), new Vector2(12, -36), new Vector2(316, 372),
                font, 13, FontStyle.Normal, Color.white);
            _texto.alignment = TextAnchor.UpperLeft;
            _texto.horizontalOverflow = HorizontalWrapMode.Wrap;

            _titulo.text = "";
            _texto.text = "Clic en un elemento (columna/viga/muro) para inspeccionarlo.\n" +
                          "Clic en el fondo o presiona Escape para deseleccionar.";
        }

        static Text NewText(Transform parent, string name, Vector2 anchorMin, Vector2 anchorMax,
            Vector2 pos, Vector2 size, Font font, int fs, FontStyle s, Color c)
        {
            var go = NewRect(parent, name, anchorMin, anchorMax, pos, size);
            var t = go.gameObject.AddComponent<Text>();
            t.font = font;
            t.fontSize = fs;
            t.fontStyle = s;
            t.color = c;
            t.alignment = TextAnchor.UpperLeft;
            return t;
        }

        static RectTransform NewRect(Transform parent, string name, Vector2 anchorMin,
            Vector2 anchorMax, Vector2 pos, Vector2 size)
        {
            var go = new GameObject(name, typeof(RectTransform));
            go.transform.SetParent(parent, false);
            var rt = (RectTransform)go.transform;
            rt.anchorMin = anchorMin;
            rt.anchorMax = anchorMax;
            rt.anchoredPosition = pos;
            rt.sizeDelta = size;
            return rt;
        }

        void Update()
        {
            if (Input.GetKeyDown(KeyCode.Escape)) Deselect();
        }
    }
}