package com.nemove.calorieyar;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.Locale;

public final class FoodDatabase {
    private FoodDatabase() {}

    public static final List<FoodItem> FOODS = Arrays.asList(
        new FoodItem("egg", "تخم‌مرغ", "عدد متوسط", 72, 6.3, 0.4, 4.8),
        new FoodItem("fried_egg", "نیمرو", "عدد", 105, 6.3, 0.5, 8.2),
        new FoodItem("sangak", "نان سنگک", "کف دست", 75, 2.5, 15, 0.5),
        new FoodItem("barbari", "نان بربری", "کف دست", 85, 2.8, 17, 0.6),
        new FoodItem("lavash", "نان لواش", "ورق متوسط", 80, 2.4, 16, 0.5),
        new FoodItem("cheese", "پنیر سفید", "۳۰ گرم", 80, 5, 1, 6),
        new FoodItem("walnut", "گردو", "عدد", 26, 0.6, 0.5, 2.6),
        new FoodItem("milk", "شیر کم‌چرب", "لیوان", 110, 8, 12, 3),
        new FoodItem("tea_sugar", "چای با یک حبه قند", "استکان", 22, 0, 5.5, 0),
        new FoodItem("banana", "موز", "عدد متوسط", 105, 1.3, 27, 0.4),
        new FoodItem("apple", "سیب", "عدد متوسط", 95, 0.5, 25, 0.3),
        new FoodItem("orange", "پرتقال", "عدد متوسط", 62, 1.2, 15, 0.2),
        new FoodItem("dates", "خرما", "عدد", 23, 0.2, 6, 0),
        new FoodItem("rice", "برنج پخته", "کفگیر متوسط", 210, 4.2, 45, 0.5),
        new FoodItem("ghormeh", "قورمه‌سبزی", "ملاقه متوسط", 220, 15, 10, 13),
        new FoodItem("gheymeh", "خورش قیمه", "ملاقه متوسط", 230, 14, 16, 13),
        new FoodItem("fesenjan", "فسنجان", "ملاقه متوسط", 310, 12, 16, 23),
        new FoodItem("zereshk", "زرشک‌پلو با مرغ", "پرس متوسط", 680, 37, 82, 22),
        new FoodItem("joojeh", "جوجه کباب", "سیخ", 260, 34, 3, 12),
        new FoodItem("koobideh", "کباب کوبیده", "سیخ", 300, 24, 2, 22),
        new FoodItem("tomato_grill", "گوجه کبابی", "عدد", 25, 1, 5, 0.2),
        new FoodItem("doogh", "دوغ", "لیوان", 75, 3, 7, 3),
        new FoodItem("yogurt", "ماست کم‌چرب", "پیاله", 90, 6, 9, 3),
        new FoodItem("lentil_rice", "عدس‌پلو", "بشقاب متوسط", 520, 16, 91, 10),
        new FoodItem("loobia_rice", "لوبیاپلو", "بشقاب متوسط", 560, 18, 82, 17),
        new FoodItem("tahchin", "ته‌چین مرغ", "برش متوسط", 420, 21, 48, 16),
        new FoodItem("ash", "آش رشته", "کاسه متوسط", 310, 13, 45, 9),
        new FoodItem("haleem", "حلیم", "کاسه متوسط", 350, 18, 46, 10),
        new FoodItem("falafel", "ساندویچ فلافل", "عدد", 520, 16, 72, 19),
        new FoodItem("bandari", "ساندویچ بندری", "عدد", 590, 20, 63, 27),
        new FoodItem("omelet", "املت گوجه", "بشقاب کوچک", 260, 13, 10, 19),
        new FoodItem("kotlet", "کتلت", "عدد متوسط", 180, 9, 15, 10),
        new FoodItem("salad", "سالاد شیرازی", "کاسه", 70, 2, 13, 1),
        new FoodItem("nuts", "آجیل مخلوط", "مشت کوچک", 170, 5, 7, 15),
        new FoodItem("cake", "کیک ساده", "برش متوسط", 260, 4, 35, 12),
        new FoodItem("chocolate", "شکلات", "۲۰ گرم", 110, 1.5, 12, 7),
        new FoodItem("cola", "نوشابه", "قوطی ۳۳۰ml", 140, 0, 35, 0),
        new FoodItem("coffee", "قهوه ساده", "فنجان", 5, 0.3, 0.5, 0),
        new FoodItem("latte", "لاته", "لیوان متوسط", 170, 9, 15, 8),
        new FoodItem("water", "آب", "لیوان", 0, 0, 0, 0)
    );

    public static final List<ActivityType> ACTIVITIES = Arrays.asList(
        new ActivityType("walk_easy", "پیاده‌روی آرام", 2.8),
        new ActivityType("walk_fast", "پیاده‌روی تند", 4.3),
        new ActivityType("run", "دویدن", 8.3),
        new ActivityType("treadmill", "تردمیل متوسط", 6.0),
        new ActivityType("cycling", "دوچرخه‌سواری", 6.8),
        new ActivityType("strength", "بدنسازی", 5.0),
        new ActivityType("football", "فوتبال / فوتسال", 7.0),
        new ActivityType("swim", "شنا", 6.0),
        new ActivityType("yoga", "یوگا", 2.5),
        new ActivityType("pilates", "پیلاتس", 3.0),
        new ActivityType("stairs", "بالا رفتن از پله", 8.0),
        new ActivityType("hiking", "کوهنوردی", 6.5),
        new ActivityType("rope", "طناب زدن", 10.0),
        new ActivityType("housework", "کارهای خانه", 3.0)
    );

    public static List<FoodItem> search(String q) {
        if (q == null || q.trim().isEmpty()) return new ArrayList<>(FOODS);
        String s = q.trim().toLowerCase(Locale.ROOT);
        List<FoodItem> out = new ArrayList<>();
        for (FoodItem food : FOODS) if (food.name.toLowerCase(Locale.ROOT).contains(s)) out.add(food);
        return out;
    }
}
