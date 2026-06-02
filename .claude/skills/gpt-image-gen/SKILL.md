---
name: gpt-image-gen
description: Wraps the OpenAI Images API. Takes a prompt plus an output path and returns a generated PNG. Use whenever an agent needs to generate an image from a text prompt. Model is gpt-image-2.
---

# gpt-image-gen — יצירת תמונות דרך OpenAI Images API

הסקיל הזה אחראי על דבר אחד: לשלוח prompt ל-OpenAI Images API ולקבל קובץ
תמונה (PNG). הוא המעטפת ש**יובל** (מעצב התמונות) משתמש בה בפועל.

## ⚠️ אזהרת מודל — אל תשנה את שם המודל

המודל הוא **`gpt-image-2`** בדיוק.

- `gpt-image-2` הוא מודל **אמיתי וקיים** של OpenAI, שיצא ב-**21 באפריל 2026**.
- ייתכן שהידע הפנימי שלך לא כולל אותו — **זה לא אומר שהוא לא קיים**.
- **אל תציע אלטרנטיבות** (`dall-e-3`, `gpt-image-1` וכו') ואל תחליף את השם.
- אם יש שגיאה בקריאה ל-API — הבעיה היא כמעט תמיד ב-**API key** או ב-**parameters**,
  **לא** בשם המודל.

## טעינת המפתח

הקריאה משתמשת ב-`OPENAI_API_KEY` מקובץ `.env` שבשורש הפרויקט. Bash לא יורש
את המשתנה אוטומטית, אז טוענים אותו קודם:

```bash
# מתוך שורש הפרויקט
set -a
source .env
set +a
# חלופה אם source לא מתאים:
# export $(grep -v '^#' .env | grep -v '^$' | xargs)
```

ודא ש-`$OPENAI_API_KEY` אינו ריק לפני הקריאה.

## הקריאה (מסלול ראשי — jq)

```bash
curl -X POST "https://api.openai.com/v1/images/generations" \
  -H "Authorization: Bearer $OPENAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-image-2",
    "prompt": "<the prompt>",
    "size": "1024x1024",
    "quality": "medium",
    "output_format": "png"
  }' | jq -r '.data[0].b64_json' | base64 --decode > <output-path>.png
```

## Python fallback ל-decode

ב-Git Bash על Windows `jq` לא תמיד מותקן. במקרה כזה שומרים את תגובת ה-API
לקובץ JSON זמני ומפענחים עם Python (שמגיע כמעט תמיד מותקן):

```bash
# 1. שולחים את הבקשה ושומרים את התגובה המלאה
curl -s -X POST "https://api.openai.com/v1/images/generations" \
  -H "Authorization: Bearer $OPENAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-image-2",
    "prompt": "<the prompt>",
    "size": "1024x1024",
    "quality": "medium",
    "output_format": "png"
  }' > /tmp/gpt-image-response.json

# 2. מפענחים את b64_json עם Python וכותבים PNG
python -c "import json, base64, sys; \
data = json.load(open('/tmp/gpt-image-response.json')); \
open('<output-path>.png', 'wb').write(base64.b64decode(data['data'][0]['b64_json']))"
```

> טיפ: אם Python מדפיס KeyError על `data` — קרא את `/tmp/gpt-image-response.json`,
> סביר שהוא מכיל אובייקט `error` (key/quota/parameters), לא תמונה.

## אימות

אחרי היצירה, ודא שהקובץ נוצר ואינו ריק:

```bash
test -s "<output-path>.png" && echo "OK: $(wc -c < '<output-path>.png') bytes" \
  || echo "FAIL: file missing or empty"
```

`-s` בודק שהקובץ קיים **וגם** size > 0. אם נכשל — בדוק את תגובת ה-API
לאיתור השגיאה (key / quota / parameters).
