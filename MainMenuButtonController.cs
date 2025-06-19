using UnityEngine;
using UnityEngine.SceneManagement;

public class MainMenuButtonController : MonoBehaviour
{
    public void StartGomoku()
    {
        SceneManager.LoadScene("GomokuScene");
    }

    public void StartFurnitureControl()
    {
        SceneManager.LoadScene("FurnitureScene");
    }

    public void ExitGame()
    {
        Application.Quit();
#if UNITY_EDITOR
        UnityEditor.EditorApplication.isPlaying = false;
#endif
    }
}