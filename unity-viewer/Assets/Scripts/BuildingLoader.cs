using System.Collections.Generic;
using System.IO;
using Newtonsoft.Json;
using Newtonsoft.Json.Linq;
using UnityEngine;

namespace Edificio.Viewer
{
    public static class BuildingLoader
    {
        public const string DataDir = "json";
        public static string DataPath => Path.Combine(Application.streamingAssetsPath, DataDir);

        public static Dictionary<int, Vector3> LoadNodos()
        {
            var file = JsonConvert.DeserializeObject<NodoFile>(Read("nodos.json"));
            var map = new Dictionary<int, Vector3>();
            foreach (var n in file.nodos) map[n.tag] = new Vector3(n.x, n.z, n.y);
            return map;
        }

        public static GrillaFile LoadGrilla()
        {
            return JsonConvert.DeserializeObject<GrillaFile>(Read("grilla.json"));
        }

        public static List<ElementoJson> LoadElementos()
        {
            return JsonConvert.DeserializeObject<ElementoFile>(Read("elementos.json")).elementos;
        }

        public static Dictionary<int, TributariaViga> LoadTributarias()
        {
            var file = JsonConvert.DeserializeObject<TribFile>(Read("tributarias.json"));
            var map = new Dictionary<int, TributariaViga>();
            if (file?.vigas == null) return map;
            foreach (var v in file.vigas) map[v.elementTag] = v;
            return map;
        }

        public static List<ApoyoJson> LoadApoyos()
        {
            return JsonConvert.DeserializeObject<ApoyoFile>(Read("apoyos.json")).apoyos;
        }

        static string Read(string name)
        {
            var path = Path.Combine(DataPath, name);
            if (!File.Exists(path))
            {
                Debug.LogError($"No se encontro {path}. Copia results/export/*.json a Assets/StreamingAssets/json/");
                return "{}";
            }
            return File.ReadAllText(path);
        }
    }

    public enum TipoColor
    {
        Columna,
        Viga,
        Voladizo,
        Diagonal,
        Muro,
        Nodo,
        Apoyo
    }

    public static class BuildingColors
    {
        static readonly Dictionary<TipoColor, Color> Paleta = new Dictionary<TipoColor, Color>
        {
            { TipoColor.Columna,  new Color(0.80f, 0.22f, 0.20f) },      // rojo
            { TipoColor.Viga,     new Color(0.13f, 0.47f, 0.71f) },      // azul
            { TipoColor.Voladizo, new Color(0.00f, 0.72f, 0.72f) },      // cian
            { TipoColor.Diagonal, new Color(0.20f, 0.63f, 0.28f) },      // verde
            { TipoColor.Muro,     new Color(0.90f, 0.62f, 0.22f) },      // naranja
            { TipoColor.Nodo,     new Color(0.15f, 0.15f, 0.15f) },      // gris
            { TipoColor.Apoyo,    new Color(0.35f, 0.85f, 0.35f) },      // verde claro
        };

        public static Color Get(TipoColor t) => Paleta[t];
    }
}