using System.IO;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.SceneManagement;

namespace Edificio.Viewer.EditorTools
{
    public static class SceneAutoBuild
    {
        const string ScenePath = "Assets/Scenes/Main.unity";

        const string BakedPref = "Edificio.Viewer.SceneCreated";

        [InitializeOnLoadMethod]
        static void OnInit()
        {
            EditorApplication.delayCall += () =>
            {
                if (SessionState.GetBool(BakedPref, false)) return;
                SessionState.SetBool(BakedPref, true);
                EnsureScene();
            };
        }

        [MenuItem("Edificio/Verificar JSON")]
        public static void VerifyJson()
        {
            var nodos = BuildingLoader.LoadNodos();
            var elementos = BuildingLoader.LoadElementos();
            var trib = BuildingLoader.LoadTributarias();
            var grilla = BuildingLoader.LoadGrilla();
            var apoyos = BuildingLoader.LoadApoyos();
            Debug.Log(string.Format(
                "VERIFY nodos={0} elementos={1} tributarias={2} apoyos={3} ejesX={4} ejesY={5} niveles={6}",
                nodos?.Count, elementos?.Count, trib?.Count, apoyos?.Count,
                grilla?.ejesX.Count, grilla?.ejesY.Count, grilla?.niveles.Count));
        }

        [MenuItem("Edificio/Generar escena Main")]
        public static void EnsureScene()
        {
            if (File.Exists(ScenePath)) return;

            var scene = EditorSceneManager.NewScene(NewSceneSetup.DefaultGameObjects, NewSceneMode.Single);

            var viewer = new GameObject("Viewer");
            viewer.AddComponent<MainViewer>();

            Directory.CreateDirectory("Assets/Scenes");
            EditorSceneManager.SaveScene(scene, ScenePath);

            var settings = new EditorBuildSettingsScene[1];
            settings[0] = new EditorBuildSettingsScene(ScenePath, true);
            EditorBuildSettings.scenes = settings;

            Debug.Log($"Edificio.Viewer: escena generada en {ScenePath}");
        }
    }
}