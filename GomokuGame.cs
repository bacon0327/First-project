using System.Collections;
using System.Collections.Generic;
using System.IO;
using UnityEngine;
using Newtonsoft.Json;
using TMPro; // 引用 TextMeshPro
using UnityEngine.UI;

public class GomokuGame : MonoBehaviour
{
    public GameObject blackStonePrefab;
    public GameObject whiteStonePrefab;

    // 顯示「歷史紀錄」的 UI 元件
    public TextMeshProUGUI moveHistoryText;
    // 顯示「目前輪到誰」或「誰勝利」的 UI 元件
    private TextMeshProUGUI turnStatusText;
    private string lastJsonContent = "";
    private string currentPlayer = "黑子";
    private string jsonPath;
    private Dictionary<string, string> boardState = new Dictionary<string, string>();
    private List<GameObject> placedStones = new List<GameObject>();
    private List<string> moveHistory = new List<string>();
    private bool gameEnded = false;

    // 自動取得 spacing
    private float gridSpacing = 1.5f;
    private ChessboardGenerator boardGenerator;

    void Start()
    {
        boardGenerator = FindObjectOfType<ChessboardGenerator>();
        if (boardGenerator != null)
        {
            gridSpacing = boardGenerator.spacing;
            Debug.Log("已自動從棋盤取得 spacing 值: " + gridSpacing);
        }
        else
        {
            Debug.LogWarning("未找到 ChessboardGenerator，將使用預設 spacing: " + gridSpacing);
        }

        // 建立歷史紀錄 Canvas
        CreateHistoryCanvas();

        // 建立右側提示欄
        CreateTurnStatusText();

        // 設定攝影機
        SetCameraAboveBoard();

        // 啟動 JSON 監聽
        jsonPath = Path.Combine(Application.streamingAssetsPath, "step.json");
        Debug.Log("JSON 檔案路徑: " + jsonPath);

        // ⛔ 避免讀到上次的內容（初始化 lastJsonContent）
        if (File.Exists(jsonPath))
        {
            lastJsonContent = File.ReadAllText(jsonPath);
            Debug.Log("已略過初始 JSON 內容。等待下一次變化才執行。");
        }
        StartCoroutine(CheckJsonLoop());
    }

    void CreateHistoryCanvas()
    {
        GameObject canvasObj = new GameObject("WorldCanvas", typeof(Canvas), typeof(CanvasScaler), typeof(GraphicRaycaster));
        Canvas canvas = canvasObj.GetComponent<Canvas>();
        canvas.renderMode = RenderMode.WorldSpace;

        RectTransform rect = canvas.GetComponent<RectTransform>();
        rect.sizeDelta = new Vector2(600, 900); // 更大面板
        canvasObj.transform.position = new Vector3(-4f, 1f, 10f); // 靠近棋盤左側中央
        canvasObj.transform.rotation = Quaternion.Euler(90, 0, 0);
        canvasObj.transform.localScale = new Vector3(0.01f, 0.01f, 0.01f); // 避免太巨大

        CanvasScaler scaler = canvasObj.GetComponent<CanvasScaler>();
        scaler.dynamicPixelsPerUnit = 10;

        // 建立 Text
        GameObject textObj = new GameObject("MoveHistoryText", typeof(TextMeshProUGUI));
        textObj.transform.SetParent(canvasObj.transform, false);

        TextMeshProUGUI tmp = textObj.GetComponent<TextMeshProUGUI>();
        tmp.fontSize = 70;
        tmp.alignment = TextAlignmentOptions.TopLeft;
        tmp.enableWordWrapping = false;
        tmp.text = "歷史紀錄：";

        // ⚠️ 指定中文字型（需放 Resources/Fonts/）
        TMP_FontAsset chineseFont = Resources.Load<TMP_FontAsset>("Fonts/NotoSansTC-Regular SDF");
        if (chineseFont != null)
        {
            tmp.font = chineseFont;
        }
        else
        {
            Debug.LogWarning("未找到中文字型 NotoSansTC-Regular SDF，將使用預設字體。");
        }

        RectTransform textRect = tmp.GetComponent<RectTransform>();
        textRect.sizeDelta = new Vector2(600, 900); // 填滿 Canvas

        moveHistoryText = tmp;
    }

    void CreateTurnStatusText()
    {
        GameObject canvasObj = new GameObject("TurnStatusCanvas", typeof(Canvas), typeof(CanvasScaler), typeof(GraphicRaycaster));
        Canvas canvas = canvasObj.GetComponent<Canvas>();
        canvas.renderMode = RenderMode.WorldSpace;

        RectTransform rect = canvas.GetComponent<RectTransform>();
        rect.sizeDelta = new Vector2(100, 900);
        canvasObj.transform.position = new Vector3(18f, 1f, 13f); // 根據你的棋盤右邊位置調整
        canvasObj.transform.rotation = Quaternion.Euler(90, 0, 0);
        canvasObj.transform.localScale = new Vector3(0.01f, 0.01f, 0.01f);

        CanvasScaler scaler = canvasObj.GetComponent<CanvasScaler>();
        scaler.dynamicPixelsPerUnit = 10;

        // 建立 Text
        GameObject textObj = new GameObject("TurnStatusText", typeof(TextMeshProUGUI));
        textObj.transform.SetParent(canvasObj.transform, false);

        TextMeshProUGUI tmp = textObj.GetComponent<TextMeshProUGUI>();
        tmp.fontSize = 100;
        tmp.alignment = TextAlignmentOptions.TopLeft;
        tmp.enableWordWrapping = true;
        tmp.overflowMode = TextOverflowModes.Overflow;
        tmp.alignment = TextAlignmentOptions.TopLeft;
        tmp.verticalAlignment = VerticalAlignmentOptions.Top;
        tmp.text = "目前輪到：黒子下棋";

        // 指定中文字型（需已存在）
        TMP_FontAsset chineseFont = Resources.Load<TMP_FontAsset>("Fonts/NotoSansTC-Regular SDF");
        if (chineseFont != null)
        {
            tmp.font = chineseFont;
        }
        else
        {
            Debug.LogWarning("未找到中文字型 NotoSansTC-Regular SDF，將使用預設字體。");
        }

        RectTransform textRect = tmp.GetComponent<RectTransform>();
        textRect.sizeDelta = new Vector2(400, 200);

        // 綁定給欄位
        turnStatusText = tmp;
    }



    void SetCameraAboveBoard()
    {
        int boardSize = 15;
        float spacing = gridSpacing;
        if (boardGenerator != null)
        {
            boardSize = boardGenerator.boardSize;
        }
        float center = (boardSize + 1) / 2f * spacing;
        float height = boardSize * spacing * 1.2f;

        if (Camera.main != null)
        {
            Camera.main.transform.position = new Vector3(center, height, center);
            Camera.main.transform.rotation = Quaternion.Euler(90, 0, 0);
        }
    }

    IEnumerator CheckJsonLoop()
    {
        while (true)
        {
            if (gameEnded) yield break;

            if (File.Exists(jsonPath))
            {
                string jsonContent = File.ReadAllText(jsonPath);
                if (jsonContent != lastJsonContent && !string.IsNullOrWhiteSpace(jsonContent))
                {
                    lastJsonContent = jsonContent;
                    try
                    {
                        StepData stepData = JsonConvert.DeserializeObject<StepData>(jsonContent);
                        if (stepData != null && !string.IsNullOrEmpty(stepData.玩家棋子顏色) && !string.IsNullOrEmpty(stepData.下的格子))
                        {
                            HandleMove(stepData);
                        }
                        else
                        {
                            CommandData commandData = JsonConvert.DeserializeObject<CommandData>(jsonContent);
                            if (commandData != null && !string.IsNullOrEmpty(commandData.遊戲指令))
                            {
                                HandleCommand(commandData);
                            }
                            else
                            {
                                Debug.Log("錯誤：JSON 格式無法識別，請確認是下棋步驟或有效指令。");
                                if (turnStatusText != null)
                                {
                                    turnStatusText.text = "錯誤：JSON 格式無法識別，請確認是下棋步驟或有效指令。";
                                }
                            }
                        }
                    }
                    catch (System.Exception ex)
                    {
                        Debug.Log("JSON 格式錯誤，請重新確認。錯誤訊息：" + ex.Message);
                        if (turnStatusText != null)
                        {
                            turnStatusText.text = "JSON 格式錯誤，請重新確認。錯誤訊息：" + ex.Message;
                        }
                    }
                }
            }

            yield return new WaitForSeconds(1f);
        }
    }

    void HandleMove(StepData data)
    {
        if (data.玩家棋子顏色 != currentPlayer)
        {
            Debug.Log("錯誤：輪到 " + currentPlayer + " 下，請重新說一次要下的位置");
            if (turnStatusText != null)
            {
                turnStatusText.text = "錯誤：輪到 " + currentPlayer + " 下，請重新說一次要下的位置";
            }
            return;
        }

        if (boardState.ContainsKey(data.下的格子))
        {
            Debug.Log("錯誤：格子已有棋子，請重新說一次要下的位置");
            if (turnStatusText != null)
            {
                turnStatusText.text = "錯誤：格子已有棋子，請重新說一次要下的位置";
            }
            return;
        }

        Vector3 pos = ParsePosition(data.下的格子);
        GameObject prefab = (data.玩家棋子顏色 == "黑子") ? blackStonePrefab : whiteStonePrefab;
        GameObject newStone = Instantiate(prefab, pos, Quaternion.identity);
        placedStones.Add(newStone);
        boardState[data.下的格子] = data.玩家棋子顏色;

        RecordMove(data.玩家棋子顏色, data.下的格子);

        if (CheckWin(data.下的格子, data.玩家棋子顏色))
        {
            Debug.Log(data.玩家棋子顏色 + " 勝利！");
            gameEnded = true;

            // 顯示勝利狀態
            if (turnStatusText != null)
            {
                turnStatusText.text = "HEY " + data.玩家棋子顏色 + " 勝利！";
            }
            return;
        }

        currentPlayer = (currentPlayer == "黑子") ? "白子" : "黑子";
        Debug.Log("目前輪到: " + currentPlayer + " 下棋。");
        if (turnStatusText != null)
        {
            turnStatusText.text = "目前輪到: " + currentPlayer + " 下棋。";
        }
    }

    void RecordMove(string playerColor, string grid)
    {
        string moveEntry = $"{playerColor} 下在 {grid}";
        moveHistory.Add(moveEntry);

        if (moveHistory.Count > 20)
            moveHistory.RemoveAt(0);

        Debug.Log("--- 下棋歷史 (最近20筆) ---");
        foreach (string move in moveHistory)
            Debug.Log(move);
        Debug.Log("--------------------------");

        if (moveHistoryText != null)
            moveHistoryText.text = string.Join("\n", moveHistory);
    }

    void HandleCommand(CommandData command)
    {
        Debug.Log("接收到指令: " + command.遊戲指令);
        switch (command.遊戲指令)
        {
            case "投降":
                string winner = (currentPlayer == "黑子") ? "白子" : "黑子";
                Debug.Log(currentPlayer + " 投降，" + winner + " 勝利！");
                if (turnStatusText != null)
                {
                    turnStatusText.text = currentPlayer + " 投降，" + winner + " 勝利！";
                }
                gameEnded = true;
                break;
            case "關閉遊戲":
                Debug.Log("關閉遊戲指令已執行。");
                if (turnStatusText != null)
                {
                    turnStatusText.text = "關閉遊戲指令已執行。";
                }
                gameEnded = true;
        #if UNITY_EDITOR
                UnityEditor.EditorApplication.isPlaying = false;
        #else
                Application.Quit();
        #endif
                break;
            case "悔棋":
                UndoLastMove();
                break;
            case "重置棋盤":
                ResetBoard();
                break;
            default:
                Debug.Log("未知指令: " + command.遊戲指令);
                if (turnStatusText != null)
                {
                    turnStatusText.text = "未知指令: " + command.遊戲指令;
                }
                break;
        }

    }

    void UndoLastMove()
    {
        if (placedStones.Count == 0)
        {
            Debug.Log("沒有棋子可以悔。");
            if (turnStatusText != null)
            {
                turnStatusText.text = "沒有棋子可以悔。";
            }
            return;
        }

        GameObject lastStone = placedStones[^1];
        Destroy(lastStone);
        placedStones.RemoveAt(placedStones.Count - 1);

        if (moveHistory.Count > 0)
        {
            string lastMoveString = moveHistory[^1];
            string[] parts = lastMoveString.Split(' ');
            if (parts.Length == 3)
            {
                string gridKey = parts[2];
                if (boardState.ContainsKey(gridKey))
                {
                    boardState.Remove(gridKey);
                    moveHistory.RemoveAt(moveHistory.Count - 1);
                    currentPlayer = (currentPlayer == "黑子") ? "白子" : "黑子";
                    Debug.Log("悔棋成功，目前輪到: " + currentPlayer + " 下棋。");
                    if (turnStatusText != null)
                    {
                        turnStatusText.text = "悔棋成功，目前輪到: " + currentPlayer + " 下棋。";
                    }
                }
            }
        }

        if (moveHistoryText != null){
            moveHistoryText.text = string.Join("\n", moveHistory);
        }

        
    }

    Vector3 ParsePosition(string 格子名)
    {
        string[] parts = 格子名.Split('之');
        if (parts.Length != 2)
        {
            Debug.LogError("格子名稱格式錯誤: " + 格子名 + "。應為 'X之Y' 格式。");
            if (turnStatusText != null)
            {
                turnStatusText.text = "格子名稱格式錯誤: " + 格子名 + "。應為 'X之Y' 格式。";
            }
            return Vector3.zero;
        }

        int x = int.Parse(parts[0]);
        int z = int.Parse(parts[1]);
        return new Vector3(x * gridSpacing, 0.5f, z * gridSpacing);
    }

    bool CheckWin(string posKey, string color)
    {
        string[] parts = posKey.Split('之');
        if (parts.Length != 2)
        {
            Debug.LogError("檢查勝利時格子名稱格式錯誤: " + posKey);
            return false;
        }

        int x = int.Parse(parts[0]);
        int y = int.Parse(parts[1]);

        Vector2Int[] directions = {
            new Vector2Int(1, 0), new Vector2Int(0, 1),
            new Vector2Int(1, 1), new Vector2Int(1, -1)
        };

        foreach (var dir in directions)
        {
            int count = 1;
            count += CountStones(x, y, dir.x, dir.y, color);
            count += CountStones(x, y, -dir.x, -dir.y, color);
            if (count >= 5) return true;
        }
        return false;
    }

    int CountStones(int x, int y, int dx, int dy, string color)
    {
        int count = 0;
        for (int step = 1; step < 5; step++)
        {
            int nx = x + dx * step;
            int ny = y + dy * step;
            string key = nx + "之" + ny;

            if (boardState.ContainsKey(key) && boardState[key] == color)
                count++;
            else
                break;
        }
        return count;
    }
    void ResetBoard()
    {
        // 清除棋子
        foreach (var stone in placedStones)
        {
            Destroy(stone);
        }
        placedStones.Clear();

        // 清除狀態與歷史紀錄
        boardState.Clear();
        moveHistory.Clear();
        gameEnded = false;
        currentPlayer = "黑子";

        // 清除畫面上文字
        if (moveHistoryText != null)
            moveHistoryText.text = "";

        Debug.Log("棋盤已重置。黑子重新開始下棋。");
        if (turnStatusText != null)
        {
            turnStatusText.text = "棋盤已重置。黑子重新開始下棋。";
        }
    }


    [System.Serializable]
    public class StepData
    {
        public string 玩家棋子顏色;
        public string 下的格子;
    }

    [System.Serializable]
    public class CommandData
    {
        public string 遊戲指令;
    }
}
