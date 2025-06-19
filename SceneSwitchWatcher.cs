using UnityEngine;
using UnityEngine.SceneManagement;
using System.Collections;
using System.IO;
using Newtonsoft.Json;

public class SceneSwitchWatcher : MonoBehaviour
{
    private string lastJsonContent = "";
    private string jsonPath;

    void Awake()
    {
        DontDestroyOnLoad(this.gameObject); // 場景切換時保留此物件
        jsonPath = Path.Combine(Application.streamingAssetsPath, "change.json");

        if (File.Exists(jsonPath))
        {
            lastJsonContent = File.ReadAllText(jsonPath);
        }

        StartCoroutine(CheckJsonLoop());
    }

    IEnumerator CheckJsonLoop()
    {
        while (true)
        {
            if (File.Exists(jsonPath))
            {
                string jsonContent = File.ReadAllText(jsonPath);

                if (jsonContent != lastJsonContent && !string.IsNullOrWhiteSpace(jsonContent))
                {
                    lastJsonContent = jsonContent;

                    try
                    {
                        SelectionData data = JsonConvert.DeserializeObject<SelectionData>(jsonContent);

                        if (data != null && !string.IsNullOrEmpty(data.選擇的項目))
                        {
                            if (data.選擇的項目 == "五子棋" && SceneManager.GetActiveScene().name != "GomokuScene")
                            {
                                SceneManager.LoadScene("GomokuScene");
                            }
                            else if (data.選擇的項目 == "家具控制" && SceneManager.GetActiveScene().name != "FurnitureScene")
                            {
                                SceneManager.LoadScene("FurnitureScene");
                            }
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
