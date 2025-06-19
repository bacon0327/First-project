using UnityEngine;

public class ChessboardGenerator : MonoBehaviour
{
    public GameObject gridPrefab; // 棋盤格子 (方塊預製體)
    public int boardSize = 14;    // 棋盤邊長（15x15）
    public float spacing = 1.4f;  // 格子間距
    public Material lineMaterial; // ⚠️ 新增一個黑線材質（可用 Unity 預設的 Unlit/Color 黑）

    void Start()
    {
        for (int x = 1; x <= boardSize; x++)
        {
            for (int y = 1; y <= boardSize; y++)
            {
                // 改為從左下角開始擺放（Z 軸由小到大）
                Vector3 pos = new Vector3(x * spacing, 0, y * spacing);

                // 生成格子
                GameObject grid = Instantiate(gridPrefab, pos, Quaternion.identity);

                // 命名：照你原本的格式，例如 "1之1"
                grid.name = x + "之" + y;

                // 設為子物件
                grid.transform.parent = this.transform;

                // 設定 CellInfo
                CellInfo info = grid.GetComponent<CellInfo>();
                if (info != null)
                {
                    info.row = x;
                    info.col = y;
                    info.currentState = CellState.Empty;
                }
            }
        }
                DrawGridLines();
                AddAxisLabels();
    }

    void AddAxisLabels()
    {
        for (int i = 1; i <= boardSize; i++)
        {
            // 建立 X 軸數字（橫向）在 Z = 0 位置
            CreateLabel(i.ToString(), new Vector3(i * spacing, 0.02f, 0f));
    
            // 建立 Z 軸數字（縱向）在 X = 0 位置
            CreateLabel(i.ToString(), new Vector3(0f, 0.02f, i * spacing));
        }
    }

    void CreateLabel(string text, Vector3 position)
    {
        GameObject textObj = new GameObject("Label_" + text);
        textObj.transform.position = position;
        textObj.transform.rotation = Quaternion.Euler(90, 0, 0); // 面向上方
        textObj.transform.parent = this.transform;

        TextMesh textMesh = textObj.AddComponent<TextMesh>();
        textMesh.text = text;
        textMesh.characterSize = 0.2f;
        textMesh.fontSize = 40;
        textMesh.color = Color.black;
        textMesh.anchor = TextAnchor.MiddleCenter;
    }


    void DrawGridLines()
    {
        float size = spacing * boardSize;
        float offset = spacing;

        for (int i = 1; i <= boardSize; i++)
        {
            // 垂直線
            CreateLine(new Vector3(i * spacing, 0.01f, spacing), new Vector3(i * spacing, 0.01f, size));
            // 水平線
            CreateLine(new Vector3(spacing, 0.01f, i * spacing), new Vector3(size, 0.01f, i * spacing));
        }
    }

    void CreateLine(Vector3 start, Vector3 end)
    {
        GameObject line = new GameObject("GridLine");
        line.transform.parent = this.transform;
        LineRenderer lr = line.AddComponent<LineRenderer>();
        lr.material = lineMaterial;
        lr.startWidth = 0.05f;
        lr.endWidth = 0.05f;
        lr.positionCount = 2;
        lr.SetPosition(0, start);
        lr.SetPosition(1, end);
    }
}
