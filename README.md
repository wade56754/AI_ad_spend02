# AI骞垮憡浠ｆ姇绯荤粺

> 馃殌 **椤圭洰鐗堟湰**: v2.1
> 馃搮 **鏈€鍚庢洿鏂?*: 2025-11-12
> 馃捇 **鎶€鏈爤**: FastAPI + PostgreSQL + Supabase + Python

---

## 馃搵 椤圭洰姒傝堪

AI骞垮憡浠ｆ姇绯荤粺鏄竴涓熀浜嶧astAPI鍜孲upabase鐨勭幇浠ｅ寲骞垮憡鎶曟斁绠＄悊骞冲彴锛屾彁渚涘畬鏁寸殑骞垮憡璐︽埛绠＄悊銆佹秷鑰楄窡韪€佸厖鍊煎鎵广€佹暟鎹璐︾瓑鍔熻兘銆?
### 鏍稿績鍔熻兘
- 馃幆 **椤圭洰绠＄悊** - 澶氶」鐩€佸瀹㈡埛绠＄悊
- 馃搳 **鏁版嵁杩借釜** - 瀹炴椂骞垮憡娑堣€楀拰绾跨储缁熻
- 馃挵 **璐㈠姟瀹℃壒** - 鍏呭€肩敵璇枫€佸鎵规祦绋?- 馃搱 **鏁版嵁鍒嗘瀽** - CPL銆丷OI绛夊叧閿寚鏍囧垎鏋?- 馃攼 **鏉冮檺绠＄悊** - 鍩轰簬瑙掕壊鐨勮闂帶鍒?
---

## 馃彈锔?绯荤粺鏋舵瀯

```
鈹屸攢鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹?    鈹屸攢鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹?    鈹屸攢鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹?鈹?  鍓嶇 (React)   鈹傗攢鈹€鈹€鈹€鈻垛攤  鍚庣 (FastAPI)  鈹傗攢鈹€鈹€鈹€鈻垛攤  鏁版嵁搴?PostgreSQL)鈹?鈹?                鈹?    鈹?                鈹?    鈹?                鈹?鈹?- 鐢ㄦ埛鐣岄潰       鈹?    鈹?- RESTful API   鈹?    鈹?- 涓氬姟鏁版嵁       鈹?鈹?- 鏁版嵁灞曠ず       鈹?    鈹?- 涓氬姟閫昏緫       鈹?    鈹?- 瀹¤鏃ュ織       鈹?鈹?- 浜や簰鎿嶄綔       鈹?    鈹?- 鏉冮檺鎺у埗       鈹?    鈹?- 鍏崇郴瀹屾暣鎬?    鈹?鈹斺攢鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹?    鈹斺攢鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹?    鈹斺攢鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹?                                鈻?                                鈹?                        鈹屸攢鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹?                        鈹?  Supabase      鈹?                        鈹?                鈹?                        鈹?- 瀹炴椂璁㈤槄       鈹?                        鈹?- 鏂囦欢瀛樺偍       鈹?                        鈹?- 璁よ瘉鏈嶅姟       鈹?                        鈹斺攢鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹?```

---

## 馃殌 蹇€熷紑濮?
### 鐜瑕佹眰
- Python 3.8+
- PostgreSQL 12+
- Node.js 16+ (鍓嶇)

### 1. 鍏嬮殕椤圭洰
```bash
git clone https://github.com/your-org/ai_ad_spend02.git
cd ai_ad_spend02
```

### 2. 鏁版嵁搴撹缃?```bash
# 浣跨敤鎻愪緵鐨勮剼鏈垵濮嬪寲鏁版嵁搴?cd scripts/database
python create_admin_simple.py

# 鎴栨墜鍔ㄦ墽琛孲QL鏂囦欢
psql $DATABASE_URL -f 01_init_database_supabase.sql
```

### 3. 鍚庣鍚姩
```bash
# 鍒涘缓铏氭嫙鐜
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 瀹夎渚濊禆
pip install -r requirements.txt

# 閰嶇疆鐜鍙橀噺
cp .env.example .env
# 缂栬緫 .env 鏂囦欢锛屽～鍏ュ繀瑕侀厤缃?
# 鍚姩鏈嶅姟
uvicorn backend.main:app --reload
```

### 4. 鍓嶇鍚姩锛堝鏋滄湁锛?```bash
cd frontend
npm install
npm start
```

---

## 馃摎 鏂囨。涓績

### 馃摉 蹇呰鏂囨。
- [馃搵 鏂囨。绱㈠紩](docs/DOCUMENTATION_INDEX.md) - 瀹屾暣鏂囨。瀵艰埅
- [馃敡 寮€鍙戣鑼僝(docs/development/DEVELOPMENT_STANDARDS.md) - 缂栫爜瑙勮寖鍜屾渶浣冲疄璺?- [馃梽锔?鏁版嵁搴撹璁(docs/core/DATA_SCHEMA_v2_3.md) - 瀹屾暣鏁版嵁搴撶粨鏋?
### 馃殌 閮ㄧ讲鎸囧崡
- [馃摝 閮ㄧ讲鎸囧崡](docs/deployment/DEPLOYMENT_GUIDE.md) - 鐢熶骇鐜閮ㄧ讲
- [馃敀 瀹夊叏閰嶇疆](docs/deployment/SECURITY_CONFIG.md) - 瀹夊叏绛栫暐璁剧疆
- [馃搳 鐩戞帶杩愮淮](docs/deployment/MONITORING_OPS.md) - 绯荤粺鐩戞帶鏂规

### 馃洜锔?寮€鍙戞寚鍗?- [馃彈锔?绯荤粺姒傝](docs/core/SYSTEM_OVERVIEW.md) - 鏋舵瀯璁捐璇存槑
- [鈿欙笍 鐘舵€佹満璁捐](docs/core/STATE_MACHINE.md) - 涓氬姟娴佺▼鐘舵€佺鐞?- [馃攲 API寮€鍙戞寚鍗梋(docs/development/BACKEND_API_GUIDE.md) - 鍚庣API瑙勮寖

### 馃搳 鏁版嵁搴撴枃妗?- [馃梽锔?鏁版嵁搴撹璁(docs/core/DATA_SCHEMA_v2_3.md) - 瀹屾暣鏁版嵁妯″瀷
- [馃敡 鏁版嵁搴撹剼鏈琞(scripts/database/README.md) - 鍒濆鍖栧拰缁存姢鑴氭湰
- [馃摑 SQL鏌ヨ绀轰緥](docs/database/queries/) - 甯哥敤鏌ヨ绀轰緥

---

## 馃敡 寮€鍙戝伐鍏?
### VS Code閰嶇疆
1. 瀹夎鎺ㄨ崘鎵╁睍锛?   ```
   - Supabase (supabase.supabase)
   - Python (ms-python.python)
   - SQLTools (mtxr.sqltools)
   ```

2. 鎵撳紑宸ヤ綔鍖猴細
   ```bash
   code ai-ad-spend.code-workspace
   ```

### 鏁版嵁搴撹繛鎺?```bash
# 涓绘暟鎹簱
Host: db.jzmcoivxhiyidizncyaq.supabase.co
Port: 5432
Database: postgres
User: postgres
```

---

## 馃搧 椤圭洰缁撴瀯

```
ai_ad_spend02/
鈹溾攢鈹€ app/                    # 鍚庣搴旂敤浠ｇ爜
鈹?  鈹溾攢鈹€ api/               # API璺敱
鈹?  鈹溾攢鈹€ core/              # 鏍稿績閰嶇疆
鈹?  鈹溾攢鈹€ models/            # 鏁版嵁妯″瀷
鈹?  鈹溾攢鈹€ services/          # 涓氬姟鏈嶅姟
鈹?  鈹斺攢鈹€ utils/             # 宸ュ叿鍑芥暟
鈹溾攢鈹€ scripts/               # 鑴氭湰宸ュ叿
鈹?  鈹斺攢鈹€ database/          # 鏁版嵁搴撶浉鍏宠剼鏈?鈹溾攢鈹€ docs/                  # 椤圭洰鏂囨。
鈹?  鈹溾攢鈹€ core/              # 鏍稿績璁捐鏂囨。
鈹?  鈹溾攢鈹€ development/       # 寮€鍙戞寚鍗?鈹?  鈹斺攢鈹€ deployment/        # 閮ㄧ讲鏂囨。
鈹溾攢鈹€ frontend/              # 鍓嶇浠ｇ爜锛堝鏋滄湁锛?鈹溾攢鈹€ tests/                 # 娴嬭瘯浠ｇ爜
鈹溾攢鈹€ requirements.txt       # Python渚濊禆
鈹斺攢鈹€ README.md             # 椤圭洰璇存槑
```

---

## 馃И 娴嬭瘯

### 杩愯娴嬭瘯
```bash
# 杩愯鎵€鏈夋祴璇?pytest

# 杩愯鐗瑰畾娴嬭瘯
pytest tests/test_api.py

# 鐢熸垚娴嬭瘯瑕嗙洊鐜囨姤鍛?pytest --cov=app tests/
```

### API娴嬭瘯
```bash
# 鍋ュ悍妫€鏌?curl http://localhost:8000/health

# API鏂囨。
http://localhost:8000/docs
```

---

## 馃攧 CI/CD

椤圭洰閰嶇疆浜嗚嚜鍔ㄥ寲娴佺▼锛?- **浠ｇ爜妫€鏌?*: Black, Flake8, MyPy
- **娴嬭瘯**: pytest
- **鏂囨。鐢熸垚**: Sphinx
- **閮ㄧ讲**: Docker + Kubernetes

---

## 馃 璐＄尞鎸囧崡

1. Fork椤圭洰
2. 鍒涘缓鍔熻兘鍒嗘敮 (`git checkout -b feature/AmazingFeature`)
3. 鎻愪氦鏇存敼 (`git commit -m 'Add some AmazingFeature'`)
4. 鎺ㄩ€佸埌鍒嗘敮 (`git push origin feature/AmazingFeature`)
5. 鍒涘缓Pull Request

### 寮€鍙戣鑼?- 閬靛惊 [PEP 8](https://www.python.org/dev/peps/pep-0008/)
- 缂栧啓鍗曞厓娴嬭瘯
- 鏇存柊鐩稿叧鏂囨。
- 浣跨敤鏈夋剰涔夌殑鎻愪氦淇℃伅

---

## 馃摑 鏇存柊鏃ュ織

### v2.1 (2025-11-12)
- 鉁?鏂板Supabase闆嗘垚
- 馃敡 浼樺寲鏁版嵁搴撶粨鏋?- 馃摎 瀹屽杽鏂囨。浣撶郴
- 馃洜锔?閲嶆瀯API鏋舵瀯

### v2.0 (2025-10-20)
- 馃殌 绯荤粺閲嶆瀯
- 馃搳 鏂板鏁版嵁鍒嗘瀽鍔熻兘
- 馃攼 澧炲己瀹夊叏鐗规€?
[鏌ョ湅瀹屾暣鏇存柊鏃ュ織](CHANGELOG.md)

---

## 馃摓 鏀寔

- 馃摟 **閭**: dev@aiad.com
- 馃搵 **闂鍙嶉**: [GitHub Issues](https://github.com/your-org/ai_ad_spend02/issues)
- 馃挰 **璁ㄨ**: [GitHub Discussions](https://github.com/your-org/ai_ad_spend02/discussions)
- 馃摉 **鏂囨。**: [椤圭洰鏂囨。涓績](docs/DOCUMENTATION_INDEX.md)

---

## 馃搫 璁稿彲璇?
鏈」鐩噰鐢?[MIT License](LICENSE) - 鏌ョ湅 [LICENSE](LICENSE) 鏂囦欢浜嗚В璇︽儏

---

## 馃檹 鑷磋阿

鎰熻阿鎵€鏈変负杩欎釜椤圭洰鍋氬嚭璐＄尞鐨勫紑鍙戣€咃紒

---

<div align="center">
  Made with 鉂わ笍 by AI骞垮憡浠ｆ姇绯荤粺鍥㈤槦
</div>






## 🔌 接口文档入口
- [🧭 接口文档索引](docs/development/API_DOCUMENTATION_INDEX.md)
- [📚 接口开发指南（实现基线）](docs/development/API_DEVELOPMENT_GUIDE.md)
- [🔌 后端API开发手册](docs/development/BACKEND_API_GUIDE.md)
- [🧪 测试实施任务清单](docs/development/TESTING_IMPLEMENTATION_TASKS.md)
- [✅ 代码质量任务清单](docs/development/CODE_QUALITY_TASKS.md)
- [🚀 部署发布任务清单](docs/development/DEPLOYMENT_RELEASE_TASKS.md)

