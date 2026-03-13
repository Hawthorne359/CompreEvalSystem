# 接口：辅导员/主任「负责班级」下的学生列表（扩展用）

## 用途

查询**某用户通过 UserRole 负责的班级**下的所有学生。  
适用于：辅导员、院系主任等拥有 `scope_type='class'`、`scope_id=班级ID` 的用户，汇总其负责范围内学生，便于后续做统计、导出或单独页面。

## 请求

- **方法**: `GET`
- **路径**: `/api/v1/responsible-class-students/`
- **Query**: `user_id`（必填）— 要查询的用户 ID（通常为辅导员/主任等）
- **鉴权**: 需登录；仅**管理员**或**本人**可调（本人只能查自己的负责班级学生）

## 响应

- **200**:  
  - `user_id`: 被查询用户 ID  
  - `responsible_class_ids`: 该用户负责的班级 ID 列表（来自 UserRole scope_type='class' 的 scope_id）  
  - `students`: 上述班级下的学生列表（即 `class_obj_id in responsible_class_ids` 的用户），格式同 `UserListSerializer` 列表项

- **400**: 未传 `user_id`  
- **403**: 无权限（非管理员且非本人）  
- **404**: 用户不存在  

## 示例

```http
GET /api/v1/responsible-class-students/?user_id=5
Authorization: Bearer <access_token>
```

```json
{
  "user_id": 5,
  "responsible_class_ids": [1, 2, 3],
  "students": [
    { "id": 10, "username": "s20210101", "name": "张一", ... },
    ...
  ]
}
```

## 后续扩展建议

- 在「组织架构」或「用户管理」中增加入口：选择某辅导员后，调用本接口展示其负责班级学生。
- 可在此基础上做：按辅导员导出 Excel、负责范围内测评统计等。
