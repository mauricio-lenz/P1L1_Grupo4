using UnityEngine;

namespace Edificio.Viewer
{
    public class ElementItem : MonoBehaviour
    {
        public ElementoJson element;
        public TributariaViga trib;
        public string etiqueta { get; private set; }

        Color _base;
        bool _sel;

        public void Setup(ElementoJson el, TributariaViga t)
        {
            element = el;
            trib = t;
            etiqueta = el.elementTag.HasValue ? "V" + el.elementTag : el.nombre;
            _base = GetComponent<Renderer>().material.color;
            SetSelected(false);
        }

        public void SetSelected(bool sel)
        {
            _sel = sel;
            if (Application.isPlaying)
            {
                var r = GetComponent<Renderer>();
                if (r != null && _base != default(Color))
                    r.material.color = sel ? Color.yellow : _base;
            }
        }
    }
}