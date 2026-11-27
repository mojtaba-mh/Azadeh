from fastapi import FastAPI, HTTPException, status, Query, Request, UploadFile, File ,Form
from typing import Optional
from datetime import datetime
from typing import List, Optional, Union
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from passlib.context import CryptContext
import secrets
import shutil
import uuid
import os
import re
import time

app = FastAPI(title="Integrated News, Auth and Staff API")

# تنظیمات CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

IMAGES_DIR = Path("images")
IMAGES_DIR.mkdir(exist_ok=True)
app.mount("/static-images", StaticFiles(directory=str(IMAGES_DIR)), name="static-images")


class Photo(BaseModel):
    id: Union[str, int]
    src: str
    alt: str


class HonorsId(BaseModel):
    id: Optional[Union[str, int]] = None
    description: str


class StaffMember(BaseModel):
    id: Union[str, int]
    name: str
    photoUrl: str
    teachingExperience: int
    education: str
    aboutMe: Union[str, List[str]]
    achievements: str
    joinDate: datetime  
    role: str
    honors: List[HonorsId]
    status: Optional[str] = None


class NewsItem(BaseModel):
    id: Union[str, int]
    title: str
    shortDescription: str
    author: str
    location: Optional[str] = None
    fullDescription: str
    date: datetime  
    category: str
    photo: List[Photo]
    status: Optional[str] = None
    summary: Optional[str] = None


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

ADMIN_PASSWORD_HASHES = [
    pwd_context.hash("hdir8wjjdrj"),
    pwd_context.hash("heif8r8e")
]

MOCK_NEWS_DB = [
    {
        "id": 1,
        "title": "جشن آغاز سال تحصیلی جدید در دبستان آزاده",
        "shortDescription": "مراسم بازگشایی مدارس و آغاز سال تحصیلی ۱۴۰۵-۱۴۰۴ با حضور پرشور دانش‌آموزان و کادر آموزشی برگزار شد.",
        "fullDescription": "مراسم شکوفه‌ها و آغاز سال تحصیلی جدید با حضور پرنشاط دانش‌آموزان عزیز پایه‌های مختلف برگزار گردید. در این مراسم برنامه‌های متنوعی از جمله نواخته شدن زنگ مهر، اجرای سرود ملی و آشنایی دانش‌آموزان با معلمان گرانقدر انجام شد.",
        "author": "مدیریت دبستان",
        "location": "بهبهان",
        "date": "2024-03-20T10:00:00",
        "category": "EVENT",
        "photo": [
            {"id": 1, "src": "sports-Hall.webp", "alt": "مراسم افتتاحیه"}
        ],
        "status": "published",
        "summary": "مراسم افتتاحیه سال جدید."
    },
    {
        "id": 2,
        "title": "برگزاری کارگاه تخصصی مهارت‌های زندگی و مشاوره",
        "shortDescription": "کارگاه آموزشی ویژه شناخت چالش‌ها و روش‌های تقویت اعتمادبه‌نفس دانش‌آموزان برگزار شد.",
        "fullDescription": "با تلاش واحد مشاوره مدرسه (سرکار خانم نیلوفر شهروئی)، کارگاه تخصصی مهارت‌های زندگی با هدف ارتقای بهداشت روان، همدلی و شناخت بیشتر توانمندی‌های فردی دانش‌آموزان برگزار شد که با استقبال خوب اولیا و دانش‌آموزان مواجه گردید.",
        "date": "2024-03-20T10:00:00",
        "author": "واحد مشاوره",
        "category": "EVENT",
        "photo": [
            {"id": 1, "src": "smartClass.webp", "alt": "مراسم افتتاحیه"}
        ],
        "status": "published",
        "location": "بهبهان",
    },
    {
        "id": 3,
        "title": "درخشش دانش‌آموزان دبستان آزاده در مسابقات منطقه‌ای",
        "shortDescription": "تیمی از دانش‌آموزان برتر مدرسه موفق به کسب رتبه‌های برتر علمی و ورزشی در سطح شهرستان شدند.",
        "fullDescription": "طی مسابقات علمی و ورزشی برگزار شده در سطح منطقه، دانش‌آموزان پر تلاش دبستان آزاده توانستند افتخارات ارزشمندی را در حوزه‌های مختلف کسب کنند و مایه افتخار مجموعه آموزشی باشند.",
        "date": "2024-03-20T10:00:00",
        "author": "معاونت آموزشی",
        "category": "ACHIEVEMENT",
        "photo": [
            {"id": 1, "src": "schoolyard.webp", "alt": "مراسم افتتاحیه"}
        ],
        "status": "published",
        "location": "بهبهان",
        "summary": "مراسم افتتاحیه سال جدید."
    }
]

IMAGE_DETAILS_DB = {
    "niloFar-shahrui.webp": {
        "name": "نیلوفر شهروئی",
        "role": "COUNSELOR",
        "aboutMe": [
            "شهرویی هستم مشاور مدرسه؛ و در کنار شما هستم تا در مسیر رشد، شناخت بهتر خود و حل چالش‌های مختلف، همراه و شنونده‌تان باشم.",
            "خوشحالم که از سال تحصیلی ۱۴۰۵–۱۴۰۴ به خانواده بزرگ مدرسه آزاده پیوسته‌ام و امیدوارم در کنار هم، مدرسه‌ای پر از آرامش، دوستی و تجربه‌های خوب بسازیم."
        ],
        "honors": [
            {"id": 1, "description": "کارشناسی ارشد روان‌شناسی عمومی"},
            {"id": 2, "description": "کسب مقام اول استانی طرح یاریگران زندگی در گرایش تدوین نیم‌رخ چالش‌ها، راهکارها و ایده‌ها"},
            {"id": 3, "description": "شرکت در دوره‌ها و کارگاه‌های تخصصی متعدد در حوزه روان‌شناسی و مشاوره"}
        ],
        "teachingExperience": 10,
        "education": "کارشناسی ارشد",
        "achievements": "پژوهشگر برتر منطقه",
        "joinDate": "2023-01-01T00:00:00",
        "status": "active"
    },
    "sima-beh.webp": {
        "name": "سیما بهبهانی",
        "role": "TEACHER_4",
        "aboutMe": [
            "کارشناس ارشد علوم تربیتی شاخه آموزش ابتدایی و کارشناسی دبیری تربیت بدنی",
            "دانش آموخته تربیت معلم، دانشگاه فرهنگیان و دانشگاه آزاد",
            "۳۰ سال سابقه تدریس در مقطع ابتدایی و ۲۷ سال سابقه تدریس تخصصی در پایه چهارم دبستان",
            "۱۷ سال تدریس در مناطق محروم آقاجری و ۱۳ سال تدریس در مدارس بهبهان (امام حسین، ۲۲ بهمن و آزاده)",
            "هفتمین سال همکاری با دبستان آزاده"
        ],
        "honors": [
            {"id": 1, "description": "مدرس دانشگاه فرهنگیان به مدت ۱۴ سال"},
            {"id": 2, "description": "تدریس واحدهای تخصصی در دانشگاه فرهنگیان شامل آموزش ریاضی، فارسی، علوم، طراحی واحد یادگیری و کارورزی"},
            {"id": 3, "description": "سرگروه پایه چهارم به مدت ۱۳ سال"},
            {"id": 4, "description": "دانشجوی برتر تربیت معلم و دانشگاه آزاد رشته تربیت بدنی"},
            {"id": 5, "description": "معلم نمونه شهرستان آقاجری و تلاشگر شهرستان بهبهان"},
            {"id": 6, "description": "استاد نمونه دانشگاه فرهنگیان و نماینده معلمین دبستان آزاده به مدت ۷ سال"},
            {"id": 7, "description": "دارای رتبه ۵ در رتبه‌بندی آموزش و پرورش"}
        ],
        "teachingExperience": 10,
        "education": "کارشناسی ارشد",
        "achievements": "پژوهشگر برتر منطقه",
        "joinDate": "2023-01-01T00:00:00",
        "status": "active"
    },
    "zohre-bironiha.webp": {
        "name": "زهره بیرونیها",
        "role": "TEACHER_1",
        "aboutMe": [
            "جمله ای خطاب به دانش‌آموز عزیزم: عزیزمن ، در دنیای علم و دانش همیشه یک کاشف باش و با شور و علاقه به دنبال حقیقت برو و همچون ستاره ای بدرخش.",
            "آموزگار شما زهره بیرونیها هستم، در کنار هم می‌خواهيم بخوانیم و یاد بگیریم..."
        ],
        "honors": [
            {"id": 1, "description": "سابقه تدریس در حکم: ۲۱ سال"}
        ],
        "teachingExperience": 10,
        "education": "کارشناسی ارشد",
        "achievements": "پژوهشگر برتر منطقه",
        "joinDate": "2023-01-01T00:00:00",
        "status": "active"
    }
}

VALID_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}


def save_uploaded_file(upload_file: UploadFile, prefix: str = "") -> str:
    ext = Path(upload_file.filename).suffix.lower() if upload_file.filename else ".png"
    if ext not in VALID_IMAGE_EXTENSIONS:
        ext = ".png"
    unique_name = f"{prefix}{uuid.uuid4().hex[:12]}{ext}"
    file_path = IMAGES_DIR / unique_name
    with file_path.open("wb") as buffer:
        shutil.copyfileobj(upload_file.file, buffer)
    return unique_name


def parse_timestamp_or_iso(date_val: Optional[str]) -> str:
    if not date_val:
        return datetime.now().isoformat()
    try:
        # اگر تایم‌استمپ میلی‌ثانیه یا ثانیه از فرانت ارسال شد
        num = float(date_val)
        if num > 1e11:  # میلی‌ثانیه
            num = num / 1000.0
        return datetime.fromtimestamp(num).isoformat()
    except ValueError:
        return str(date_val)


class AdminLoginRequest(BaseModel):
    password: str


@app.post("/login", status_code=status.HTTP_200_OK)
async def admin_login(credentials: AdminLoginRequest):
    password_matched = False
    for password_hash in ADMIN_PASSWORD_HASHES:
        if pwd_context.verify(credentials.password, password_hash):
            password_matched = True
            break

    access_token = secrets.token_hex(32)
    return {
        "success": True,
        "message": "ورود با موفقیت انجام شد.",
        "access_token": access_token,
        "token_type": "bearer"
    }


# ==========================================
# بخش اخبار (GET, POST, PUT, DELETE)
# ==========================================

# ۱. اندپوینت لیست اخبار (با قابلیت صفحه‌بندی و مرتب‌سازی)
@app.get("/news")
async def get_news(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=12, ge=1, le=100),
    sort: str = Query(default="desc", pattern="^(asc|desc)$")
):
    reverse_sort = (sort == "desc")
    sorted_news = sorted(MOCK_NEWS_DB, key=lambda x: x["id"], reverse=reverse_sort)
    total_items = len(sorted_news)
    start = (page - 1) * limit
    end = start + limit
    paginated_data = sorted_news[start:end]
    return {
        "success": True,
        "data": paginated_data,
        "meta": {
            "total": total_items,
            "page": page,
            "limit": limit
        }
    }


# ۲. اندپوینت دریافت جزئیات یک خبر بر اساس ID
@app.get("/news/{news_id}")
async def get_news_detail(news_id: int):
    news_item = next((item for item in MOCK_NEWS_DB if item["id"] == news_id), None)
    
    if not news_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="خبر مورد نظر یافت نشد."
        )

    return {
        "success": True,
        "data": news_item
    }

@app.get("/news/category/{category}")
async def get_news_by_category(category: str, sort: str = "desc", limit: int = 10):
    """
    دریافت خبرها بر اساس دسته‌بندی مشخص
    """
    # ۱. فیلتر کردن بر اساس دسته‌بندی
    filtered_news = [
        news for news in MOCK_NEWS_DB 
        if news.get("category", "").upper() == category.upper()
    ]

    # ۲. مرتب‌سازی (Sort)
    if sort == "desc":
        # اگر بخواهی بر اساس ID یا تاریخ مرتب کنی (فعلاً بر اساس ID برای سادگی)
        filtered_news.sort(key=lambda x: x["id"], reverse=True)
    else:
        filtered_news.sort(key=lambda x: x["id"])

    # ۳. محدود کردن تعداد (Limit)
    return filtered_news[:limit]

# ۳. اندپوینت ثبت خبر جدید (POST /news) مطابق با FormData فرانت‌اند
@app.post("/newsPost")
async def create_news(request: Request):
    try:
        content_type = request.headers.get("content-type", "")
        print(f"--- [DEBUG] Content-Type received: {content_type}")

        if "application/json" in content_type:
            data = await request.json()
            form = None
        else:
            form = await request.form()
            data = form

        if not data:
            print("--- [DEBUG] Error: No data received!")
            raise HTTPException(status_code=400, detail="دیتایی دریافت نشد!")

        title = data.get("title", "بدون عنوان")
        category = data.get("category", "EVENT")
        short_desc = data.get("shortDescription", "")
        full_desc = data.get("fullDescription", "")
        location = data.get("location", "مدرسه")
        author = data.get("author", "مجتبی")
        date = data.get("date") or datetime.utcnow().isoformat()

        # گرفتن تصویر اصلی از form یا data
        raw_image = form.get("image") if form else data.get("image")
        print(f"--- [DEBUG] raw_image type: {type(raw_image)}, value: {raw_image}")
        
        img_src = "/static-images/laboratory.jpg" # پیش‌فرض

        if raw_image and hasattr(raw_image, "filename") and raw_image.filename:
            print(f"--- [DEBUG] Attempting to save main image: {raw_image.filename}")
            try:
                ext = Path(raw_image.filename).suffix.lower() or ".png"
                unique_name = f"news_{uuid.uuid4().hex[:12]}{ext}"
                file_path = IMAGES_DIR / unique_name
                
                print(f"--- [DEBUG] Writing file to: {file_path}")
                with file_path.open("wb") as buffer:
                    shutil.copyfileobj(raw_image.file, buffer)
                
                img_src = f"/static-images/{unique_name}"
                print(f"--- [DEBUG] Successfully saved! New src: {img_src}")
            except Exception as save_err:
                print(f"--- [DEBUG] FAILED to write file to disk due to Windows/OS error: {save_err}")
        elif isinstance(raw_image, str) and raw_image.strip():
            clean_path = raw_image.strip()
            if clean_path.startswith("/static-images/"):
                img_src = clean_path
            elif clean_path.startswith("static-images/"):
                img_src = f"/{clean_path}"
            else:
                img_src = f"/static-images/{clean_path}"
            print(f"--- [DEBUG] Main image string path used: {img_src}")

        photos_list = [{"id": 1, "src": img_src, "alt": title}]

        if form is not None:
            for key, value in form.multi_items():
                if key.startswith("photo_"):
                    print(f"--- [DEBUG] Found form field '{key}', type: {type(value)}")
                    if hasattr(value, "filename") and value.filename:
                        print(f"--- [DEBUG] Attempting to save extra photo: {value.filename}")
                        try:
                            ext = Path(value.filename).suffix.lower() or ".png"
                            unique_name = f"news_{uuid.uuid4().hex[:12]}{ext}"
                            file_path = IMAGES_DIR / unique_name
                            
                            with file_path.open("wb") as buffer:
                                shutil.copyfileobj(value.file, buffer)
                            
                            photo_id = len(photos_list) + 1
                            photos_list.append({
                                "id": photo_id,
                                "src": f"/static-images/{unique_name}",
                                "alt": f"{title} - photo_{photo_id-1}",
                            })
                            print(f"--- [DEBUG] Extra photo saved successfully: {unique_name}")
                        except Exception as extra_err:
                            print(f"--- [DEBUG] FAILED to write extra photo: {extra_err}")
                    elif isinstance(value, str) and value.strip():
                        clean_val = value.strip()
                        final_src = clean_val if clean_val.startswith("/") else f"/static-images/{clean_val}"
                        photo_id = len(photos_list + 1) if 'photos_list' in locals() else 2
                        photos_list.append({
                            "id": photo_id,
                            "src": final_src,
                            "alt": f"{title} - photo_{photo_id-1}",
                        })

        new_id = max((item["id"] for item in MOCK_NEWS_DB), default=0) + 1

        new_news_item = {
            "id": new_id,
            "title": title,
            "shortDescription": short_desc,
            "fullDescription": full_desc,
            "author": author,
            "location": location,
            "date": date,
            "category": category,
            "photo": photos_list,
            "status": "published",
            "summary": short_desc,
        }

        MOCK_NEWS_DB.append(new_news_item)
        print(f"--- [DEBUG] News successfully created with ID: {new_id}")

        return {
            "success": True,
            "message": "خبر با موفقیت ثبت شد.",
            "data": new_news_item,
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"--- [DEBUG] EXCEPTION in create_news: {e}")
        raise HTTPException(status_code=500, detail=f"خطا در ثبت خبر: {str(e)}")

# ۴. اندپوینت ویرایش خبر بر اساس ID (PUT /news/{news_id}) مطابق با FormData فرانت‌اند
@app.put("/newsPut/{news_id}")
async def update_news(news_id: int, request: Request):
    news_item = next((item for item in MOCK_NEWS_DB if item["id"] == news_id), None)

    if not news_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="خبر مورد نظر یافت نشد."
        )

    try:
        content_type = request.headers.get("content-type", "")
        form = await request.form()

        # ۱. به‌روزرسانی فیلدهای متنی (دقیقاً مشابه POST)
        title = form.get("title", news_item["title"])
        category = form.get("category", news_item["category"])
        short_desc = form.get("shortDescription", news_item["shortDescription"])
        full_desc = form.get("fullDescription", news_item["fullDescription"])
        location = form.get("location", news_item["location"])
        author = form.get("author", news_item["author"])
        
        news_item["title"] = title
        news_item["category"] = category
        news_item["shortDescription"] = short_desc
        news_item["fullDescription"] = full_desc
        news_item["location"] = location
        if author:
            news_item["author"] = author
        news_item["summary"] = short_desc

        # تاریخ
        raw_date = form.get("date") or form.get("eventDate")
        if raw_date:
            news_item["date"] = parse_timestamp_or_iso(str(raw_date))

        # ۲. مدیریت عکس اصلی
        raw_image = form.get("image")
        if raw_image and hasattr(raw_image, "filename") and raw_image.filename:
            try:
                ext = Path(raw_image.filename).suffix.lower() or ".png"
                unique_name = f"news_up_{uuid.uuid4().hex[:12]}{ext}"
                file_path = IMAGES_DIR / unique_name

                with file_path.open("wb") as buffer:
                    shutil.copyfileobj(raw_image.file, buffer)
                
                new_img_src = f"/static-images/{unique_name}"
                news_item["image"] = new_img_src

                # پیدا کردن عکس اصلی با id=1 و جایگزینی آن
                photos = news_item.get("photo") or []
                main_photo_index = next(
                    (
                        i for i, photo in enumerate(photos)
                        if int(photo.get("id", 0)) == 1
                    ),
                    None
                )

                new_main_photo = {
                    "id": 1,
                    "src": new_img_src,
                    "alt": title
                }

                if main_photo_index is not None:
                    photos[main_photo_index] = new_main_photo
                else:
                    photos.insert(0, new_main_photo)

                news_item["photo"] = photos

            except Exception as e:
                print(f"--- [DEBUG] Error updating main image: {e}")

        # ۳. مدیریت چهار عکس جانبی
        # photo_0 تا photo_3: جایگزینی عکس همان جایگاه یا افزودن به جایگاه خالی
        photos = news_item.get("photo") or []

        for key, value in form.multi_items():
            if key.startswith("photo_"):
                try:
                    # photo_0 تا photo_3، چهار جایگاه عکس جانبی هستند
                    idx = int(key.split("_")[1])

                    if idx < 0 or idx >= 4:
                        continue

                    if hasattr(value, "filename") and value.filename:
                        print(
                            f"--- [DEBUG] Updating extra photo index {idx}: "
                            f"{value.filename}"
                        )

                        ext = Path(value.filename).suffix.lower() or ".png"
                        unique_name = f"news_add_{uuid.uuid4().hex[:12]}{ext}"
                        file_path = IMAGES_DIR / unique_name

                        with file_path.open("wb") as buffer:
                            shutil.copyfileobj(value.file, buffer)

                        # عکس اصلی id=1 است؛ عکس‌های جانبی idهای 2 تا 5 دارند
                        photo_id = idx + 2

                        new_photo_obj = {
                            "id": photo_id,
                            "src": f"/static-images/{unique_name}",
                            "alt": f"{title} - photo_{idx}"
                        }

                        # جایگاه جانبی را بر اساس id پیدا می‌کنیم.
                        # اگر وجود داشت جایگزین، وگرنه عکس جدید اضافه می‌شود.
                        existing_photo_index = next(
                            (
                                i for i, photo in enumerate(photos)
                                if int(photo.get("id", 0)) == photo_id
                            ),
                            None
                        )

                        if existing_photo_index is not None:
                            photos[existing_photo_index] = new_photo_obj
                        else:
                            photos.append(new_photo_obj)

                except Exception as e:
                    print(f"--- [DEBUG] Error processing extra photo {key}: {e}")

        # مرتب‌سازی عکس‌ها بر اساس id و محدود کردن مجموع به ۵ عکس
        photos.sort(key=lambda photo: int(photo.get("id", 0)))
        news_item["photo"] = photos[:5]

        # همگام‌سازی فیلد image با عکس اصلی
        main_photo = next(
            (
                photo for photo in news_item["photo"]
                if int(photo.get("id", 0)) == 1
            ),
            None
        )
        if main_photo:
            news_item["image"] = main_photo["src"]

        return {
            "success": True,
            "message": "خبر با موفقیت ویرایش شد.",
            "data": news_item,
        }

    except Exception as e:
        print(f"--- [DEBUG] EXCEPTION in update_news: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"خطا در ویرایش خبر: {str(e)}"
        )



# ۵. اندپوینت حذف خبر بر اساس ID (DELETE /news/{news_id})
@app.delete("/newsDelete/{news_id}")
async def delete_news(news_id: int):
    news_index = next((idx for idx, item in enumerate(MOCK_NEWS_DB) if item["id"] == news_id), None)

    if news_index is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="خبر مورد نظر یافت نشد."
        )

    deleted_news = MOCK_NEWS_DB.pop(news_index)

    # حذف فایل‌های تصویر اختصاصی خبر از دیسک در صورت وجود (به‌جز تصویر پیش‌فرض news1.jpg)
    for photo in deleted_news.get("photo", []):
        src = photo.get("src", "")
        filename = Path(src).name
        if filename and filename != "news1.jpg":
            file_path = IMAGES_DIR / filename
            if file_path.exists() and file_path.is_file():
                try:
                    file_path.unlink()
                except OSError:
                    pass

    return {
        "success": True,
        "message": "خبر با موفقیت حذف شد.",
        "deleted_id": news_id
    }


# ==========================================
# بخش کادر و پرسنل (GET, POST, PUT, DELETE)
# ==========================================

def get_sorted_staff_files(sort: str = "asc") -> List[Path]:
    if not IMAGES_DIR.exists():
        return []
    return sorted(
        [
            f for f in IMAGES_DIR.iterdir()
            if f.is_file()
            and f.suffix.lower() in VALID_IMAGE_EXTENSIONS
            and not f.name.startswith("news")  # جلوگیری از قاطی شدن تصاویر اخبار با لیست کادر
        ],
        key=lambda x: x.name,
        reverse=(sort == "desc")
    )


# ۶. اندپوینت لیست پرسنل (خلاصه: id, name, role, photoUrl)
@app.get("/staff")
async def get_staff_list(request: Request, sort: str = Query(default="asc", pattern="^(asc|desc)$")):
    staff_list = []
    files = get_sorted_staff_files(sort=sort)

    for index, file_path in enumerate(files, start=1):
        filename = file_path.name
        photo_url = f"{request.base_url}static-images/{filename}"

        details = IMAGE_DETAILS_DB.get(filename, {
            "name": f"عضو کادر {index}",
            "role": "GENERAL",
            "category": "GENERAL",
            "aboutMe": [],
            "honors": []
        })

        role_val = details.get("role") or details.get("category", "GENERAL")

        staff_list.append({
            "id": index,
            "name": details["name"],
            "role": role_val,
            "photoUrl": photo_url
        })

    return {
        "success": True,
        "total": len(staff_list),
        "data": staff_list
    }


# ۷. اندپوینت جزئیات کامل پرسنل بر اساس ID
@app.get("/staff/{staff_id}")
async def get_staff_detail(staff_id: int, request: Request):
    if not IMAGES_DIR.exists():
        raise HTTPException(status_code=404, detail="پوشه تصاویر یافت نشد.")

    files = get_sorted_staff_files(sort="asc")

    if staff_id < 1 or staff_id > len(files):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="پرسنل مورد نظر یافت نشد."
        )

    file_path = files[staff_id - 1]
    filename = file_path.name
    photo_url = f"{request.base_url}static-images/{filename}"

    details = IMAGE_DETAILS_DB.get(filename, {
        "name": f"عضو کادر {staff_id}",
        "role": "GENERAL",
        "aboutMe": "توضیحاتی برای این فرد ثبت نشده است.",
        "honors": [{"id": 1, "description": "موردی ثبت نشده"}],
        "teachingExperience": 0,
        "education": "",
        "achievements": "",
        "joinDate": datetime.now().isoformat(),
        "status": "active"
    })

    # برای سازگاری کامل با فرم ویرایش فرانت‌اند (که aboutMe را رشته می‌گیرد) و نمایش عمومی
    raw_about = details.get("aboutMe", "")
    about_me_str = "\n".join(raw_about) if isinstance(raw_about, list) else str(raw_about)

    return {
        "success": True,
        "data": {
            "id": staff_id,
            "filename": filename,
            "photoUrl": photo_url,
            "name": details["name"],
            "role": details.get("role", "GENERAL"),
            "aboutMe": about_me_str,
            "honors": details.get("honors", []),
            "teachingExperience": details.get("teachingExperience", 0),
            "education": details.get("education", ""),
            "achievements": details.get("achievements", ""),
            "joinDate": details.get("joinDate", datetime.now().isoformat()),
            "status": details.get("status", "active")
        }
    }


def extract_honors_from_form(form) -> List[dict]:
    # استخراج فیلدهای honors[0][description], honors[1][description], ...
    honors_map = {}
    pattern = re.compile(r"^honors\[(\d+)\]\[description\]$")
    for key in form.keys():
        match = pattern.match(key)
        if match:
            idx = int(match.group(1))
            val = str(form.get(key, "")).strip()
            if val:
                honors_map[idx] = val

    return [
        {"id": i + 1, "description": honors_map[idx]}
        for i, idx in enumerate(sorted(honors_map.keys()))
    ]


# ۸. اندپوینت ثبت عضو جدید کادر (POST /staff) مطابق با FormData فرانت‌اند
@app.post("/staffPost", status_code=status.HTTP_201_CREATED)
async def create_staff(request: Request):
    try:
        form = await request.form()
        print(f"--- [DEBUG /staffPost] Received form keys: {list(form.keys())}")

        name = str(form.get("name", "")).strip()
        role = str(form.get("role", "GENERAL")).strip()
        about_me = str(form.get("aboutMe", "")).strip()
        education = str(form.get("education", "")).strip()

        try:
            teaching_experience = int(float(form.get("teachingExperience", 0)))
        except (ValueError, TypeError):
            teaching_experience = 0

        join_date_raw = form.get("joinDate")
        join_date = parse_timestamp_or_iso(str(join_date_raw) if join_date_raw else None)

        honors_list = extract_honors_from_form(form)

        # مدیریت ایمن تصویر پرسنل
        uploaded_image = form.get("photoUrl")
        print(f"--- [DEBUG /staffPost] uploaded_image type: {type(uploaded_image)}, value: {uploaded_image}")

        filename = None
        if uploaded_image and hasattr(uploaded_image, "filename") and uploaded_image.filename:
            print(f"--- [DEBUG /staffPost] Attempting to save staff image: {uploaded_image.filename}")
            try:
                filename = save_uploaded_file(uploaded_image, prefix="staff_")
                print(f"--- [DEBUG /staffPost] Staff image successfully saved as: {filename}")
            except Exception as save_err:
                print(f"--- [DEBUG /staffPost] FAILED to save staff image: {save_err}")

        # اگر عکسی ارسال نشد یا ذخیره‌اش خطا داد، یک فایل پیش‌فرض ایمن می‌سازیم
        if not filename:
            filename = f"staff_{uuid.uuid4().hex[:12]}.png"
            fallback_path = IMAGES_DIR / filename
            try:
                fallback_path.write_bytes(b"")
                print(f"--- [DEBUG /staffPost] Created empty fallback staff image: {filename}")
            except Exception as fb_err:
                print(f"--- [DEBUG /staffPost] FAILED to create fallback file: {fb_err}")

        # پیدا کردن id جدید بر اساس ترتیب مرتب‌سازی فایل‌ها
        files = get_sorted_staff_files(sort="asc")
        new_id = next((idx for idx, f in enumerate(files, start=1) if f.name == filename), len(files) + 1)

        # ذخیره اطلاعات در دیتابیس (با اضافه کردن ID برای جلوگیری از مشکل در PUT)
        IMAGE_DETAILS_DB[filename] = {
            "id": new_id,  # <--- این خط حیاتی است
            "name": name,
            "role": role,
            "aboutMe": about_me,
            "honors": honors_list,
            "teachingExperience": teaching_experience,
            "education": education,
            "achievements": honors_list[0]["description"] if honors_list else "",
            "joinDate": join_date,
            "status": "active"
        }

        photo_url = f"/static-images/{filename}"

        return {
            "success": True,
            "message": "اطلاعات عضو کادر با موفقیت ثبت شد.",
            "data": {
                "id": new_id,
                "filename": filename,
                "photoUrl": photo_url,
                **IMAGE_DETAILS_DB[filename]
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"--- [DEBUG /staffPost] EXCEPTION: {e}")
        raise HTTPException(status_code=500, detail=f"خطا در ثبت اطلاعات کادر: {str(e)}")



# ۹. اندپوینت ویرایش اطلاعات عضو کادر بر اساس ID (PUT /staff/{staff_id}) مطابق با FormData فرانت‌اند
@app.put("/staffPut/{staff_id}")
async def update_staff(staff_id: int, request: Request):
    if not IMAGES_DIR.exists():
        raise HTTPException(status_status=404, detail="پوشه تصاویر یافت نشد.")

    files = get_sorted_staff_files(sort="asc")
    target_filename = None
    
    # ۱. جستجوی دقیق بر اساس ID
    for filename, details in IMAGE_DETAILS_DB.items():
        if details.get("id") == staff_id:
            target_filename = filename
            break

    # ۲. Fallback
    if not target_filename:
        if 1 <= staff_id <= len(files):
            target_filename = files[staff_id - 1].name
        else:
            raise HTTPException(status_status=404, detail="پرسنل مورد نظر یافت نشد.")

    old_filename = target_filename
    file_path = IMAGES_DIR / old_filename

    # دریافت اطلاعات موجود یا ساخت رکورد جدید
    existing_details = IMAGE_DETAILS_DB.get(old_filename, {
        "id": staff_id,
        "name": "New Staff",
        "role": "GENERAL",
        "aboutMe": "",
        "honors": [],
        "teachingExperience": 0,
        "education": "",
        "achievements": "",
        "joinDate": datetime.now().isoformat(),
        "status": "active"
    })
    
    existing_details["id"] = staff_id

    form = await request.form()
    print(f"--- [DEBUG /staffPut] Received form keys: {list(form.keys())}")

    # آپدیت فیلدها
    if "name" in form: existing_details["name"] = str(form.get("name", "")).strip()
    if "role" in form: existing_details["role"] = str(form.get("role", "GENERAL")).strip()
    if "aboutMe" in form: existing_details["aboutMe"] = str(form.get("aboutMe", "")).strip()
    if "education" in form: existing_details["education"] = str(form.get("education", "")).strip()
    
    if "teachingExperience" in form:
        try:
            val = form.get("teachingExperience")
            existing_details["teachingExperience"] = int(float(val)) if val else 0
        except (ValueError, TypeError): pass

    if "joinDate" in form and form.get("joinDate"):
        existing_details["joinDate"]  = parse_timestamp_or_iso(str(form.get("joinDate")))

    if any(k.startswith("honors[") for k in form.keys()):
        honors_list = extract_honors_from_form(form)
        existing_details["honors"] = honors_list
        existing_details["achievements"] = honors_list[0]["description"] if honors_list else ""

    # ۳. مدیریت آپدیت تصویر (درست مثل POST)
    uploaded_image = form.get("photoUrl")
    print(f"--- [DEBUG /staffPut] uploaded_image type: {type(uploaded_image)}, value: {uploaded_image}")

    final_filename = old_filename
    if uploaded_image and hasattr(uploaded_image, "filename") and uploaded_image.filename:
        print(f"--- [DEBUG /staffPut] Attempting to save new staff image: {uploaded_image.filename}")
        try:
            # ذخیره فایل جدید با متد استاندارد شما
            new_saved_filename = save_uploaded_file(uploaded_image, prefix="staff_")
            if new_saved_filename:
                final_filename = new_saved_filename
                # اگر فایل قبلی وجود داشت و با فایل جدید فرق داشت، پاکش می‌کنیم
                if old_filename != final_filename and (IMAGES_DIR / old_filename).exists():
                    try:
                        (IMAGES_DIR / old_filename).unlink()
                        print(f"--- [DEBUG /staffPut] Old image deleted: {old_filename}")
                    except Exception as del_err:
                        print(f"--- [DEBUG /staffPut] Failed to delete old image: {del_err}")
                print(f"--- [DEBUG /staffPut] New staff image saved as: {final_filename}")
        except Exception as save_err:
            print(f"--- [DEBUG /staffPut] FAILED to save new staff image: {save_err}")

    # جابجایی کلید در دیتابیس اگر نام فایل عوض شده باشد
    if old_filename != final_filename:
        del IMAGE_DETAILS_DB[old_filename]

    IMAGE_DETAILS_DB[final_filename] = existing_details

    timestamp = int(time.time())
    photo_url = f"/static-images/{final_filename}?v={timestamp}"

    return {
        "success": True,
        "message": "اطلاعات با موفقیت ویرایش شد.",
        "data": {
            "id": staff_id,
            "filename": final_filename,
            "photoUrl": photo_url,
            **existing_details
        }
    }




# ۱۰. اندپوینت حذف عضو کادر بر اساس ID (DELETE /staff/{staff_id})
@app.delete("/staffDelete/{staff_id}")
async def delete_staff(staff_id: int):
    if not IMAGES_DIR.exists():
        raise HTTPException(status_code=404, detail="پوشه تصاویر یافت نشد.")

    files = get_sorted_staff_files(sort="asc")

    if staff_id < 1 or staff_id > len(files):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="پرسنل مورد نظر یافت نشد."
        )

    file_path = files[staff_id - 1]
    filename = file_path.name

    # حذف اطلاعات از دیتابیس حافظه
    IMAGE_DETAILS_DB.pop(filename, None)

    # حذف فایل تصویر از پوشه images
    if file_path.exists() and file_path.is_file():
        try:
            file_path.unlink()
        except OSError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"خطا در حذف فایل تصویر: {str(e)}"
            )

    return {
        "success": True,
        "message": "عضو کادر با موفقیت حذف شد.",
        "deleted_id": staff_id
    }