// CellInfo.cs
using UnityEngine;

// 確保 CellState 枚舉有定義在這裡，或者在一個可以被這個檔案訪問的獨立檔案中
// (如果 CellState 在其他檔案，請確保該檔案沒有錯誤)
public enum CellState // 確保這個定義存在且沒有語法錯誤
{
    Empty,
    Occupied,
    Selected,
    MoveHighlight
    // 添加你需要的其他狀態
}

public class CellInfo : MonoBehaviour
{
    public int row;
    public int col;
    public CellState currentState; // <--- 再次確認這一行是否存在且正確！

    public void SetCoordinates(int r, int c)
    {
        row = r;
        col = c;
    }

    void Awake()
    {
        // 初始化 currentState，通常是一個好習慣
        currentState = CellState.Empty;
    }
}