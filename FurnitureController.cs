using System.Collections;
using System.IO;
using UnityEngine;
using Newtonsoft.Json;
using System.Text.RegularExpressions;

public class FurnitureController : MonoBehaviour
{
    private string lastJson = "";
    private string jsonPath;
    private float defaultOffset = 1f;
    private GameObject floorCenter;

    void Start()
    {
        CreateInitialFloor();
        jsonPath = Path.Combine(Application.streamingAssetsPath, "furniture_command.json");
        floorCenter = GameObject.Find("地板");
        PositionCameraAboveFloor();
        StartCoroutine(CheckJsonLoop());
    }

    void CreateInitialFloor()
    {
        GameObject prefab = Resources.Load<GameObject>("地板");
        if (prefab != null)
        {
            GameObject floor = Instantiate(prefab);
            floor.name = "地板";
            floor.transform.position = Vector3.zero;
        }
        else
        {
            Debug.LogWarning("找不到 Resources 裡的 '地板' 預製物件，將使用預設平面建立。 ");
            GameObject floor = GameObject.CreatePrimitive(PrimitiveType.Plane);
            floor.name = "地板";
            floor.transform.position = Vector3.zero;
            floor.transform.localScale = new Vector3(10, 1, 10);
        }
    }

    void PositionCameraAboveFloor()
    {
        Camera mainCamera = Camera.main;
        if (mainCamera != null && floorCenter != null)
        {
            Vector3 floorPos = floorCenter.transform.position;
            mainCamera.transform.position = floorPos + new Vector3(0, 870f, 0);
            mainCamera.transform.rotation = Quaternion.Euler(90f, 0f, 0f);
        }
        else
        {
            Debug.LogWarning("找不到主攝影機或地板物件，無法設定攝影機位置");
        }
    }

    IEnumerator CheckJsonLoop()
    {
        while (true)
        {
            if (File.Exists(jsonPath))
            {
                string content = File.ReadAllText(jsonPath);
                if (content != lastJson && !string.IsNullOrWhiteSpace(content))
                {
                    lastJson = content;
                    try
                    {
                        FurnitureCommand cmd = JsonConvert.DeserializeObject<FurnitureCommand>(content);
                        HandleCommand(cmd);
                    }
                    catch (System.Exception e)
                    {
                        Debug.LogError("JSON 解析錯誤: " + e.Message);
                    }
                }
            }
            yield return new WaitForSeconds(1f);
        }
    }

    void HandleCommand(FurnitureCommand cmd)
    {
        if (cmd.type != "furniture_control") return;

        if (!string.IsNullOrEmpty(cmd.距離) && (cmd.方向 == null || !cmd.方向.Contains("角")))
            defaultOffset = ParseOffset(cmd.距離);

        GameObject obj1 = GameObject.Find(cmd.object1);
        GameObject obj2 = (!string.IsNullOrEmpty(cmd.object2)) ? GameObject.Find(cmd.object2) : null;
        if (cmd.方向 == "中間") obj2 = floorCenter;

        switch (cmd.動作)
        {
            case "不想要":
            case "移除":
            case "拿掉":
                if (obj1) Destroy(obj1);
                break;

            case "放置":
            case "放入":
                if (obj1) Destroy(obj1);
                obj1 = InstantiateFromResources(cmd.object1);
                if (obj1 != null)
                {
                    obj1.name = cmd.object1;
                    obj1.transform.position = GetPlacementPosition(obj2, cmd.方向, cmd.object1);

                    // ✅ 設定預設顏色
                    SetDefaultColor(obj1);
                }
                break;

            case "移動":
                if (!obj1) return;
                Vector3 moveDir = GetDirectionVector(cmd.方向, obj1.transform, obj2);
                obj1.transform.position += moveDir * defaultOffset;
                break;

            case "旋轉":
            case "轉向":
                if (!obj1) return;
                if (obj2)
                {
                    Vector3 target = obj2.transform.position - obj1.transform.position;
                    if (target != Vector3.zero)
                        obj1.transform.rotation = Quaternion.LookRotation(target);
                    else
                        Debug.LogWarning($"{cmd.object1} 與 {cmd.object2} 重疊，無法轉向同一位置");
                }
                else
                {
                    float angle = ParseAngle(cmd.角度);
                    Vector3 axis = GetRotationAxis(cmd.方向);
                    obj1.transform.Rotate(axis, angle);
                }
                break;

            default:
                Debug.LogWarning("未知指令: " + cmd.動作);
                break;
        }
    }

    GameObject InstantiateFromResources(string name)
    {
        GameObject prefab = Resources.Load<GameObject>(name);
        if (prefab != null)
        {
            return Instantiate(prefab);
        }

        Debug.LogWarning("找不到原始家具: " + name);
        return null;
    }

    Vector3 GetPlacementPosition(GameObject refObj, string dir, string objectName)
    {
        Vector3 basePos = floorCenter != null ? floorCenter.transform.position : Vector3.zero;
        Vector3 offsetDir = GetDirectionVector(dir, null, null);

        if (dir.Contains("角"))
        {
            Renderer floorRend = floorCenter.GetComponent<Renderer>();
            float floorWidth = floorRend.bounds.size.x;
            float floorDepth = floorRend.bounds.size.z;

            Vector3 cornerOffsetVec = new Vector3(
                offsetDir.x * floorWidth * 0.5f,
                0,
                offsetDir.z * floorDepth * 0.5f
            );

            GameObject target = GameObject.Find(objectName);
            if (target != null && target.TryGetComponent<Renderer>(out Renderer objRend))
            {
                Vector3 objSize = objRend.bounds.size;
                cornerOffsetVec.x -= Mathf.Sign(offsetDir.x) * objSize.x * 0.5f;
                cornerOffsetVec.z -= Mathf.Sign(offsetDir.z) * objSize.z * 0.5f;
            }

            return basePos + cornerOffsetVec;
        }

        Vector3 offset = offsetDir * defaultOffset;
        return basePos + offset;
    }

    Vector3 GetDirectionVector(string dir, Transform self, GameObject refObj)
    {
        Camera cam = Camera.main;
        if (cam == null)
            return Vector3.right;

        Vector3 forward = Vector3.ProjectOnPlane(cam.transform.forward, Vector3.up).normalized;
        Vector3 right = Vector3.ProjectOnPlane(cam.transform.right, Vector3.up).normalized;

        switch (dir)
        {
            case "中間":
                if (refObj && self) return (refObj.transform.position - self.position).normalized;
                break;
            case "左": return -right;
            case "右": return right;
            case "前": return forward;
            case "後": return -forward;
            case "上": return Vector3.up;
            case "下": return Vector3.down;
            case "旁邊": return right;
            case "左下角": return (Vector3.left + Vector3.back).normalized;
            case "右下角": return (Vector3.right + Vector3.back).normalized;
            case "左上角": return (Vector3.left + Vector3.forward).normalized;
            case "右上角": return (Vector3.right + Vector3.forward).normalized;
        }
        return Vector3.right;
    }

    Vector3 GetRotationAxis(string dir)
    {
        switch (dir)
        {
            case "左": return Vector3.up;
            case "右": return Vector3.up;
            default: return Vector3.up;
        }
    }

    float ParseOffset(string word)
    {
        switch (word)
        {
            case "一些": return 10f;
            case "一點": return 1f;
            case "一點點": return 0.1f;
            default: return 1f;
        }
    }

    float ParseAngle(string word)
    {
        if (string.IsNullOrEmpty(word)) return 10f;
        string digits = Regex.Replace(word, "[^0-9]", "");
        if (float.TryParse(digits, out float angle)) return angle;
        return 10f;
    }

    void SetDefaultColor(GameObject obj)
    {
        if (!obj.TryGetComponent<Renderer>(out Renderer renderer)) return;

        Color color = Color.red; // 預設白色
        switch (obj.name)
        {
            case "沙發":
                color = Color.red;
                break;
            case "餐桌":
                color = new Color(0.6f, 0.4f, 0.2f); // 棕色
                break;
            case "椅子":
                color = Color.blue;
                break;
            case "床":
                color = Color.green;
                break;
            case "花瓶":
                color = Color.gray;
                break;
            case "落地燈":
                color = Color.gray;
                break;
            case "電腦":
                color = Color.gray;
                break;
            case "電腦桌":
                color = Color.gray;
                break;
            case "電腦椅":
                color = Color.gray;
                break;
           default:
                Debug.Log("未指定預設顏色的家具: " + obj.name);
                break;
        }

        renderer.material.color = color;
    }

    [System.Serializable]
    public class FurnitureCommand
    {
        public string type;
        public string object1;
        public string object2;
        public string 動作;
        public string 方向;
        public string 距離;
        public string 角度;
    }
}
