using UnityEngine;
using UnityEngine.SceneManagement;
using System.Collections;
using System.IO;
using Newtonsoft.Json;

public class MainMenuController : MonoBehaviour
{
    private string lastJsonContent = "";
    private string jsonPath;

    void Start()
    {
        jsonPath = Path.Combine(Application.streamingAssetsPath, "change.json");

        // ⚠️ 讀取初始內容但不執行切換
        if (File.Exists(jsonPath))
        {
            lastJsonContent = File.ReadAllText(jsonPath);
        }

        StartCoroutine(CheckJsonLoop());
    }

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

    IEnumerator CheckJsonLoop()
    {
        while (true)
        {
            if (File.Exists(jsonPath))
            {
                string jsonContent = File.ReadAllText(jsonPath);
    
                // ⚠️ 僅在變更時執行切換
                if (jsonContent != lastJsonContent && !string.IsNullOrWhiteSpace(jsonContent))
                {
                    lastJsonContent = jsonContent;

                    try
                    {
                        SelectionData data = JsonConvert.DeserializeObject<SelectionData>(jsonContent);
    
                        if (data != null && !string.IsNullOrEmpty(data.選擇的項目))
                        {
                            if (data.選擇的項目 == "五子棋")
                                StartGomoku();
                            else if (data.選擇的項目 == "家具控制")
                                StartFurnitureControl();
                        }
                        else
                        {
                            Debug.LogWarning("change.json 格式錯誤或資料為空。");
                        }
                    }
                    catch (System.Exception ex)
                    {
                        Debug.LogError("解析 change.json 發生錯誤：" + ex.Message);
                    }
                }
            }

            yield return new WaitForSeconds(1f);
        }
    }

    [System.Serializable]
    public class SelectionData
    {
        public string 選擇的項目;
    }
}
