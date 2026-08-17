package com.nemove.calorieyar;

import android.content.Context;
import android.content.SharedPreferences;

import org.json.JSONArray;
import org.json.JSONException;
import org.json.JSONObject;

import java.text.SimpleDateFormat;
import java.util.Date;
import java.util.Locale;

public final class DataStore {
    private static final String PREFS = "calorie_yar";
    private static final String KEY_LOGS = "logs";
    private final SharedPreferences prefs;

    public DataStore(Context context) {
        prefs = context.getSharedPreferences(PREFS, Context.MODE_PRIVATE);
    }

    public static String today() {
        return new SimpleDateFormat("yyyy-MM-dd", Locale.US).format(new Date());
    }

    public JSONArray logs() {
        try { return new JSONArray(prefs.getString(KEY_LOGS, "[]")); }
        catch (JSONException e) { return new JSONArray(); }
    }

    public void addFood(FoodItem food, double amount, String meal) {
        JSONObject o = new JSONObject();
        try {
            o.put("id", System.currentTimeMillis());
            o.put("date", today());
            o.put("type", "food");
            o.put("name", food.name + (amount == 1 ? "" : " × " + trim(amount)));
            o.put("meal", meal);
            o.put("cal", NutritionMath.foodCalories(food, amount));
            o.put("protein", food.protein * amount);
            o.put("carbs", food.carbs * amount);
            o.put("fat", food.fat * amount);
            append(o);
        } catch (JSONException ignored) {}
    }

    public void addActivity(ActivityType activity, int minutes, double weightKg) {
        JSONObject o = new JSONObject();
        try {
            o.put("id", System.currentTimeMillis());
            o.put("date", today());
            o.put("type", "activity");
            o.put("name", activity.name + " • " + minutes + " دقیقه");
            o.put("meal", "فعالیت");
            o.put("cal", NutritionMath.activityCalories(activity.met, weightKg, minutes));
            o.put("protein", 0);
            o.put("carbs", 0);
            o.put("fat", 0);
            append(o);
        } catch (JSONException ignored) {}
    }

    private void append(JSONObject o) {
        JSONArray arr = logs();
        arr.put(o);
        prefs.edit().putString(KEY_LOGS, arr.toString()).apply();
    }

    public void delete(long id) {
        JSONArray old = logs();
        JSONArray next = new JSONArray();
        for (int i = 0; i < old.length(); i++) {
            JSONObject o = old.optJSONObject(i);
            if (o != null && o.optLong("id") != id) next.put(o);
        }
        prefs.edit().putString(KEY_LOGS, next.toString()).apply();
    }

    public Totals totalsToday() {
        Totals t = new Totals();
        JSONArray arr = logs();
        String d = today();
        for (int i = 0; i < arr.length(); i++) {
            JSONObject o = arr.optJSONObject(i);
            if (o == null || !d.equals(o.optString("date"))) continue;
            if ("activity".equals(o.optString("type"))) t.burned += o.optInt("cal");
            else {
                t.eaten += o.optInt("cal");
                t.protein += o.optDouble("protein");
                t.carbs += o.optDouble("carbs");
                t.fat += o.optDouble("fat");
            }
        }
        return t;
    }

    public int getTarget() { return prefs.getInt("target", 2000); }
    public void setTarget(int v) { prefs.edit().putInt("target", Math.max(1200, v)).apply(); }
    public double getWeight() { return Double.longBitsToDouble(prefs.getLong("weight", Double.doubleToLongBits(75))); }
    public void setWeight(double v) { prefs.edit().putLong("weight", Double.doubleToLongBits(Math.max(30, v))).apply(); }
    public boolean getReminder(int id) { return prefs.getBoolean("rem_" + id, id == 4); }
    public void setReminder(int id, boolean on) { prefs.edit().putBoolean("rem_" + id, on).apply(); }

    private String trim(double d) {
        if (d == Math.rint(d)) return String.valueOf((int)d);
        return String.format(Locale.US, "%.1f", d);
    }

    public static final class Totals {
        public int eaten;
        public int burned;
        public double protein;
        public double carbs;
        public double fat;
    }
}
