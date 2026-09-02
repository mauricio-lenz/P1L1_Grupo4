using System.Collections.Generic;
using Newtonsoft.Json;

namespace Edificio.Viewer
{
    // --- nodos.json ---
    public class NodoJson
    {
        [JsonProperty("tag")] public int tag;
        [JsonProperty("x")] public float x;
        [JsonProperty("y")] public float y;
        [JsonProperty("z")] public float z;
    }

    public class NodoFile
    {
        [JsonProperty("nodos")] public List<NodoJson> nodos;
    }

    // --- grilla.json ---
    public class GrillaFile
    {
        [JsonProperty("ejes_X")] public Dictionary<string, float> ejesX;
        [JsonProperty("ejes_Y")] public Dictionary<string, float> ejesY;
        [JsonProperty("niveles")] public Dictionary<string, float> niveles;
    }

    // --- elementos.json ---
    public class ElementoJson
    {
        [JsonProperty("elementTag")] public int? elementTag;
        [JsonProperty("tipo")] public string tipo;
        [JsonProperty("nombre")] public string nombre;

        [JsonProperty("n1")] public int? n1;
        [JsonProperty("n2")] public int? n2;

        [JsonProperty("nivel")] public string nivel;
        [JsonProperty("seccion")] public string seccion;
        [JsonProperty("material")] public string material;

        [JsonProperty("transf")] public int? transf;
        [JsonProperty("orientacion")] public string orientacion;
        [JsonProperty("ix")] public int? ix;
        [JsonProperty("iy")] public int? iy;
        [JsonProperty("k")] public int? k;
        [JsonProperty("L")] public float? L;

        [JsonProperty("es_voladizo")] public bool? esVoladizo;
        [JsonProperty("linea_eje")] public string lineaEje;
        [JsonProperty("desde_eje")] public string desdeEje;
        [JsonProperty("hasta_eje")] public string hastaEje;
        [JsonProperty("eje_Y")] public string ejeY;
        [JsonProperty("desde_nivel")] public string desdeNivel;
        [JsonProperty("hasta_nivel")] public string hastaNivel;
        [JsonProperty("espesor")] public float? espesor;
    }

    public class ElementoFile
    {
        [JsonProperty("nodos")] public List<int> nodos;
        [JsonProperty("elementos")] public List<ElementoJson> elementos;
    }

    // --- tributarias.json ---
    public class TributariaViga
    {
        [JsonProperty("elementTag")] public int elementTag;
        [JsonProperty("tipo")] public string tipo;
        [JsonProperty("nivel")] public string nivel;
        [JsonProperty("orientacion")] public string orientacion;
        [JsonProperty("ix")] public int ix;
        [JsonProperty("iy")] public int iy;
        [JsonProperty("k")] public int k;
        [JsonProperty("w_kN_m")] public float wKNm;
        [JsonProperty("longitud_m")] public float longitud;
        [JsonProperty("carga_losa_kN")] public float cargaLosa;
    }

    public class TribFile
    {
        [JsonProperty("qG")] public Dictionary<string, float> qG;
        [JsonProperty("area_piso_m2")] public Dictionary<string, float> areaPiso;
        [JsonProperty("carga_total_losa_kN")] public float cargaTotalLosa;
        [JsonProperty("carga_puntual_kN")] public float cargaPuntual;
        [JsonProperty("voladizo")] public Newtonsoft.Json.Linq.JObject voladizo;
        [JsonProperty("vigas")] public List<TributariaViga> vigas;
    }

    // --- apoyos.json ---
    public class ApoyoJson
    {
        [JsonProperty("tag")] public int tag;
        [JsonProperty("ux")] public int ux;
        [JsonProperty("uy")] public int uy;
        [JsonProperty("uz")] public int uz;
        [JsonProperty("rx")] public int rx;
        [JsonProperty("ry")] public int ry;
        [JsonProperty("rz")] public int rz;
    }

    public class ApoyoFile
    {
        [JsonProperty("apoyos")] public List<ApoyoJson> apoyos;
        [JsonProperty("n")] public int n;
    }

    // --- diafragmas.json ---
    public class DiafragmaJson
    {
        [JsonProperty("nivel")] public string nivel;
        [JsonProperty("master")] public int master;
        [JsonProperty("slaves")] public List<int> slaves;
        [JsonProperty("direccion")] public int direccion;
    }

    public class DiafragmaFile
    {
        [JsonProperty("diafragmas")] public List<DiafragmaJson> diafragmas;
    }
}