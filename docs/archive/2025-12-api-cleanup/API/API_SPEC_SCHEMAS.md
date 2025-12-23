# API 规格书 JSON Schema 验证

> **文档层级**: 🔵 验证层 - 自动化检查
> **用途**: 验证 AI 输出的 API 规格书是否符合规范

---

## §1 端点定义 Schema

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "$id": "api-endpoint.schema.json",
  "title": "API Endpoint Definition",
  "type": "object",
  "required": ["method", "path", "description", "responses"],
  "properties": {
    "method": {
      "type": "string",
      "enum": ["GET", "POST", "PATCH", "PUT", "DELETE"],
      "description": "HTTP 方法"
    },
    "path": {
      "type": "string",
      "pattern": "^/[a-z][a-z0-9-]*(/:[a-z][a-zA-Z0-9]*)?(/[a-z][a-z0-9-]*)*$",
      "description": "API 路径，使用 kebab-case"
    },
    "description": {
      "type": "string",
      "minLength": 1,
      "description": "端点描述"
    },
    "permission": {
      "type": "string",
      "description": "权限要求"
    },
    "idempotent": {
      "type": "boolean",
      "description": "是否幂等"
    },
    "pathParams": {
      "type": "array",
      "items": { "$ref": "#/definitions/parameter" }
    },
    "queryParams": {
      "type": "array",
      "items": { "$ref": "#/definitions/parameter" }
    },
    "requestBody": {
      "$ref": "#/definitions/requestBody"
    },
    "responses": {
      "$ref": "#/definitions/responses"
    }
  },
  "definitions": {
    "parameter": {
      "type": "object",
      "required": ["name", "type"],
      "properties": {
        "name": {
          "type": "string",
          "pattern": "^[a-z][a-zA-Z0-9]*$",
          "description": "参数名，camelCase"
        },
        "type": {
          "type": "string",
          "enum": ["string", "number", "boolean", "array"]
        },
        "required": {
          "type": "boolean",
          "default": false
        },
        "default": {},
        "description": {
          "type": "string"
        }
      }
    },
    "requestBody": {
      "type": "object",
      "additionalProperties": {
        "$ref": "#/definitions/fieldDefinition"
      },
      "propertyNames": {
        "pattern": "^[a-z][a-zA-Z0-9]*$"
      }
    },
    "fieldDefinition": {
      "type": "object",
      "required": ["type"],
      "properties": {
        "type": {
          "type": "string",
          "enum": ["string", "number", "boolean", "array", "object"]
        },
        "required": {
          "type": "boolean",
          "default": false
        },
        "description": {
          "type": "string"
        }
      }
    },
    "responses": {
      "type": "object",
      "required": ["success"],
      "properties": {
        "success": {
          "type": "object",
          "required": ["status"],
          "properties": {
            "status": {
              "type": "integer",
              "enum": [200, 201, 204]
            },
            "body": {
              "type": "object"
            }
          }
        },
        "errors": {
          "type": "array",
          "items": {
            "$ref": "#/definitions/errorResponse"
          }
        }
      }
    },
    "errorResponse": {
      "type": "object",
      "required": ["status", "code"],
      "properties": {
        "status": {
          "type": "integer",
          "enum": [400, 401, 403, 404, 409, 422, 429, 500]
        },
        "code": {
          "type": "string",
          "enum": [
            "VALIDATION_ERROR",
            "INVALID_REQUEST",
            "UNAUTHORIZED",
            "FORBIDDEN",
            "NOT_FOUND",
            "CONFLICT",
            "DUPLICATE_ENTRY",
            "INVALID_STATUS_TRANSITION",
            "FUTURE_DATE_NOT_ALLOWED",
            "REPORT_LOCKED",
            "PROJECT_NOT_ACTIVE",
            "NOT_PROJECT_MEMBER",
            "INVALID_CREDENTIALS",
            "USER_DISABLED",
            "INSUFFICIENT_BALANCE",
            "AMOUNT_EXCEEDS_LIMIT",
            "TOO_MANY_REQUESTS",
            "INTERNAL_ERROR"
          ]
        },
        "scenario": {
          "type": "string"
        }
      }
    }
  }
}
```

---

## §2 字段名 Schema

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "$id": "api-field-names.schema.json",
  "title": "API Field Names Validation",
  "description": "验证字段名是否符合规范",
  
  "definitions": {
    "standardFieldName": {
      "type": "string",
      "enum": [
        "id",
        "createdAt",
        "updatedAt",
        "deletedAt",
        "createdBy",
        "updatedBy",
        "page",
        "pageSize",
        "total",
        "totalPages",
        "items",
        "pagination",
        "sortBy",
        "sortOrder",
        "keyword",
        "dateFrom",
        "dateTo",
        "status",
        "isActive",
        "isDeleted"
      ]
    },
    
    "forbiddenFieldName": {
      "type": "string",
      "not": {
        "pattern": "^(created_at|updated_at|deleted_at|created_by|updated_by|page_num|page_size|total_count|total_pages|sort_by|sort_order|date_from|date_to|is_active|is_deleted|ID|_id|uuid|createTime|updateTime|pageNum|pageNo|limit|offset|orderBy|startDate|endDate)$"
      }
    },
    
    "camelCaseField": {
      "type": "string",
      "pattern": "^[a-z][a-zA-Z0-9]*$",
      "description": "必须是 camelCase 格式"
    }
  }
}
```

---

## §3 响应格式 Schema

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "$id": "api-response.schema.json",
  "title": "API Response Format",
  
  "definitions": {
    "singleObjectResponse": {
      "type": "object",
      "required": ["id"],
      "properties": {
        "id": { "type": "string" },
        "createdAt": { 
          "type": "string",
          "pattern": "^\\d{4}-\\d{2}-\\d{2}T\\d{2}:\\d{2}:\\d{2}Z$"
        },
        "updatedAt": {
          "type": "string",
          "pattern": "^\\d{4}-\\d{2}-\\d{2}T\\d{2}:\\d{2}:\\d{2}Z$"
        }
      }
    },
    
    "listResponse": {
      "type": "object",
      "required": ["items", "pagination"],
      "properties": {
        "items": {
          "type": "array"
        },
        "pagination": {
          "$ref": "#/definitions/pagination"
        }
      }
    },
    
    "pagination": {
      "type": "object",
      "required": ["page", "pageSize", "total", "totalPages"],
      "properties": {
        "page": {
          "type": "integer",
          "minimum": 1
        },
        "pageSize": {
          "type": "integer",
          "minimum": 1,
          "maximum": 100
        },
        "total": {
          "type": "integer",
          "minimum": 0
        },
        "totalPages": {
          "type": "integer",
          "minimum": 0
        }
      }
    },
    
    "errorResponse": {
      "type": "object",
      "required": ["error"],
      "properties": {
        "error": {
          "type": "object",
          "required": ["code", "message"],
          "properties": {
            "code": {
              "type": "string",
              "pattern": "^[A-Z][A-Z_]*$"
            },
            "message": {
              "type": "string"
            },
            "details": {
              "type": "object",
              "additionalProperties": {
                "type": "array",
                "items": { "type": "string" }
              }
            },
            "traceId": {
              "type": "string"
            }
          }
        }
      }
    },
    
    "batchResponse": {
      "type": "object",
      "required": ["success", "failed"],
      "properties": {
        "success": {
          "type": "array",
          "items": { "type": "string" }
        },
        "failed": {
          "type": "array",
          "items": {
            "type": "object",
            "required": ["id", "error"],
            "properties": {
              "id": { "type": "string" },
              "error": {
                "type": "object",
                "required": ["code", "message"],
                "properties": {
                  "code": { "type": "string" },
                  "message": { "type": "string" }
                }
              }
            }
          }
        }
      }
    }
  }
}
```

---

## §4 时间格式 Schema

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "$id": "api-datetime.schema.json",
  "title": "DateTime Format Validation",
  
  "definitions": {
    "date": {
      "type": "string",
      "pattern": "^\\d{4}-\\d{2}-\\d{2}$",
      "description": "日期格式 YYYY-MM-DD"
    },
    
    "datetime": {
      "type": "string",
      "pattern": "^\\d{4}-\\d{2}-\\d{2}T\\d{2}:\\d{2}:\\d{2}Z$",
      "description": "时间戳格式 ISO 8601 UTC"
    },
    
    "forbiddenDatetimeFormats": {
      "type": "string",
      "not": {
        "anyOf": [
          { "pattern": "^\\d{4}/\\d{2}/\\d{2}" },
          { "pattern": "^\\d{2}-\\d{2}-\\d{4}" },
          { "pattern": "\\+\\d{2}:\\d{2}$" },
          { "pattern": "^[A-Z][a-z]{2} \\d{2}" }
        ]
      },
      "description": "禁止的时间格式"
    }
  }
}
```

---

## §5 HTTP 状态码 Schema

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "$id": "api-status-codes.schema.json",
  "title": "HTTP Status Codes Validation",
  
  "definitions": {
    "successStatusByMethod": {
      "type": "object",
      "properties": {
        "GET": { "const": 200 },
        "POST_CREATE": { "const": 201 },
        "POST_ACTION": { "const": 200 },
        "PATCH": { "const": 200 },
        "PUT": { "const": 200 },
        "DELETE": { "const": 204 }
      }
    },
    
    "errorStatusByCode": {
      "type": "object",
      "properties": {
        "VALIDATION_ERROR": { "const": 400 },
        "INVALID_REQUEST": { "const": 400 },
        "FUTURE_DATE_NOT_ALLOWED": { "const": 400 },
        "INVALID_STATUS_TRANSITION": { "const": 400 },
        "UNAUTHORIZED": { "const": 401 },
        "INVALID_CREDENTIALS": { "const": 401 },
        "FORBIDDEN": { "const": 403 },
        "NOT_PROJECT_MEMBER": { "const": 403 },
        "USER_DISABLED": { "const": 403 },
        "NOT_FOUND": { "const": 404 },
        "CONFLICT": { "const": 409 },
        "DUPLICATE_ENTRY": { "const": 409 },
        "TOO_MANY_REQUESTS": { "const": 429 },
        "INTERNAL_ERROR": { "const": 500 }
      }
    },
    
    "allowedStatusCodes": {
      "type": "integer",
      "enum": [200, 201, 204, 400, 401, 403, 404, 409, 422, 429, 500, 503]
    }
  }
}
```

---

## §6 验证脚本

### 6.1 Node.js 验证脚本

```javascript
// validate-api-spec.js
const Ajv = require('ajv');
const fs = require('fs');

const ajv = new Ajv({ allErrors: true });

// 加载 schemas
const endpointSchema = require('./api-endpoint.schema.json');
const fieldNamesSchema = require('./api-field-names.schema.json');
const responseSchema = require('./api-response.schema.json');

// 注册 schemas
ajv.addSchema(endpointSchema);
ajv.addSchema(fieldNamesSchema);
ajv.addSchema(responseSchema);

// 验证函数
function validateApiSpec(spec) {
  const errors = [];
  
  // 1. 验证字段名是否 camelCase
  const fieldNames = extractFieldNames(spec);
  fieldNames.forEach(name => {
    if (!isCamelCase(name)) {
      errors.push({
        type: 'FIELD_NAME',
        field: name,
        message: `字段名 "${name}" 不是 camelCase`
      });
    }
    if (isForbiddenName(name)) {
      errors.push({
        type: 'FORBIDDEN_NAME',
        field: name,
        message: `字段名 "${name}" 是禁止使用的名称`
      });
    }
  });
  
  // 2. 验证时间格式
  const datetimeValues = extractDatetimeValues(spec);
  datetimeValues.forEach(value => {
    if (!isValidDatetime(value)) {
      errors.push({
        type: 'DATETIME_FORMAT',
        value: value,
        message: `时间格式 "${value}" 不符合 ISO 8601 UTC`
      });
    }
  });
  
  // 3. 验证错误码
  const errorCodes = extractErrorCodes(spec);
  errorCodes.forEach(code => {
    if (!isAllowedErrorCode(code)) {
      errors.push({
        type: 'ERROR_CODE',
        code: code,
        message: `错误码 "${code}" 不在允许列表中`
      });
    }
  });
  
  // 4. 验证状态码
  const statusCodes = extractStatusCodes(spec);
  statusCodes.forEach(({ method, status }) => {
    if (!isValidStatusForMethod(method, status)) {
      errors.push({
        type: 'STATUS_CODE',
        method: method,
        status: status,
        message: `${method} 方法不应返回 ${status}`
      });
    }
  });
  
  return {
    valid: errors.length === 0,
    errors: errors
  };
}

// 辅助函数
function isCamelCase(name) {
  return /^[a-z][a-zA-Z0-9]*$/.test(name);
}

function isForbiddenName(name) {
  const forbidden = [
    'created_at', 'updated_at', 'deleted_at',
    'page_num', 'page_size', 'total_count',
    'sort_by', 'sort_order', 'date_from', 'date_to',
    'ID', '_id', 'uuid', 'createTime', 'updateTime',
    'pageNum', 'pageNo', 'limit', 'offset'
  ];
  return forbidden.includes(name);
}

function isValidDatetime(value) {
  return /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$/.test(value);
}

const allowedErrorCodes = [
  'VALIDATION_ERROR', 'INVALID_REQUEST', 'UNAUTHORIZED',
  'FORBIDDEN', 'NOT_FOUND', 'CONFLICT', 'DUPLICATE_ENTRY',
  'INVALID_STATUS_TRANSITION', 'FUTURE_DATE_NOT_ALLOWED',
  'REPORT_LOCKED', 'PROJECT_NOT_ACTIVE', 'NOT_PROJECT_MEMBER',
  'INVALID_CREDENTIALS', 'USER_DISABLED', 'INSUFFICIENT_BALANCE',
  'AMOUNT_EXCEEDS_LIMIT', 'TOO_MANY_REQUESTS', 'INTERNAL_ERROR'
];

function isAllowedErrorCode(code) {
  return allowedErrorCodes.includes(code);
}

function isValidStatusForMethod(method, status) {
  const validStatus = {
    'GET': [200],
    'POST': [200, 201],
    'PATCH': [200],
    'PUT': [200],
    'DELETE': [204]
  };
  return validStatus[method]?.includes(status);
}

module.exports = { validateApiSpec };
```

### 6.2 验证报告格式

```json
{
  "valid": false,
  "errors": [
    {
      "type": "FIELD_NAME",
      "field": "created_at",
      "message": "字段名 \"created_at\" 不是 camelCase"
    },
    {
      "type": "ERROR_CODE",
      "code": "MY_CUSTOM_ERROR",
      "message": "错误码 \"MY_CUSTOM_ERROR\" 不在允许列表中"
    },
    {
      "type": "STATUS_CODE",
      "method": "POST",
      "status": 200,
      "message": "POST 创建方法应返回 201"
    }
  ],
  "summary": {
    "totalChecks": 50,
    "passed": 47,
    "failed": 3
  }
}
```

---

## §7 在线验证工具

### 快速验证清单

AI 可以用以下正则表达式快速自检：

```javascript
// 字段名检查
const camelCaseRegex = /^[a-z][a-zA-Z0-9]*$/;

// 禁止的字段名
const forbiddenRegex = /^(created_at|updated_at|page_size|sort_by|.*_id|.*_at)$/;

// ISO 8601 UTC 时间
const datetimeRegex = /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$/;

// 日期格式
const dateRegex = /^\d{4}-\d{2}-\d{2}$/;

// URL 路径
const pathRegex = /^\/[a-z][a-z0-9-]*(\/:[a-z][a-zA-Z0-9]*)?(\/[a-z][a-z0-9-]*)*$/;
```

---

## 文档引用

- 核心规则：API_SPEC_GUIDE_v2.0_CORE.md
- 详细规范：API_SPEC_DETAILED.md
- 完整示例：API_SPEC_EXAMPLES.md
