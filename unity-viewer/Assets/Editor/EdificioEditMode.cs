using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.SceneManagement;

namespace Edificio.Viewer.EditorTools
{
    /// Genera el modelo en modo edicion para que el edificio sea visible
    /// al abrir la escena (sin necesidad de dar Play).
    [InitializeOnLoad]
    public static class EdificioEditMode
    {
        const string ScenePath = "Assets/Scenes/Main.unity";

        static EdificioEditMode()
        {
            EditorSceneManager.sceneOpened += OnSceneOpened;
            EditorApplication.delayCall += OnFirstLoad;
        }

        static void OnFirstLoad()
        {
            if (EditorApplication.isPlayingOrWillChangePlaymode) return;
            if (SceneManager.GetActiveScene().name != "Main") return;
            RebuildInEditMode();
        }

        static void OnSceneOpened(Scene scene, OpenSceneMode mode)
        {
            if (EditorApplication.isPlayingOrWillChangePlaymode) return;
            if (scene.name != "Main") return;
            RebuildInEditMode();
        }

        [MenuItem("Edificio/Reconstruir modelo visible")]
        public static void RebuildInEditMode()
        {
            var scene = SceneManager.GetActiveScene();
            if (scene.name != "Main" || !scene.isLoaded)
            {
                if (System.IO.File.Exists(ScenePath))
                    scene = EditorSceneManager.OpenScene(ScenePath, OpenSceneMode.Single);
            }

            var viewer = Object.FindObjectOfType<MainViewer>();
            if (viewer == null)
            {
                viewer = new GameObject("Viewer").AddComponent<MainViewer>();
            }
            viewer.BuildEditMode();
            EditorUtility.SetDirty(viewer);
            EditorSceneManager.MarkSceneDirty(SceneManager.GetActiveScene());
            SceneView.RepaintAll();

            // En batchmode (CI/validacion) se guarda para persistir el modelo.
            if (Application.isBatchMode)
            {
                EditorSceneManager.SaveScene(SceneManager.GetActiveScene());
            }
        }
    }
}