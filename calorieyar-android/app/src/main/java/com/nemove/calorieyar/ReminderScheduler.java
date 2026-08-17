package com.nemove.calorieyar;

import android.app.AlarmManager;
import android.app.PendingIntent;
import android.content.Context;
import android.content.Intent;

import java.util.Calendar;

public final class ReminderScheduler {
    private ReminderScheduler() {}

    private static final int[][] TIMES = {{8,30},{13,30},{18,0},{22,0}};
    private static final String[] TEXTS = {
        "صبحانه‌ات را ثبت کردی؟", "ناهارت را در کالری‌یار ثبت کن.",
        "یک نگاه کوتاه به کالری باقی‌مانده امروز بینداز.", "ثبت‌های امروزت را کامل کن."
    };

    public static void applyAll(Context context) {
        DataStore ds = new DataStore(context);
        for (int i = 1; i <= 4; i++) {
            if (ds.getReminder(i)) schedule(context, i); else cancel(context, i);
        }
    }

    public static void schedule(Context context, int id) {
        AlarmManager alarm = (AlarmManager) context.getSystemService(Context.ALARM_SERVICE);
        if (alarm == null) return;
        Calendar c = Calendar.getInstance();
        c.set(Calendar.HOUR_OF_DAY, TIMES[id-1][0]);
        c.set(Calendar.MINUTE, TIMES[id-1][1]);
        c.set(Calendar.SECOND, 0);
        c.set(Calendar.MILLISECOND, 0);
        if (c.getTimeInMillis() <= System.currentTimeMillis()) c.add(Calendar.DAY_OF_YEAR, 1);

        Intent intent = new Intent(context, ReminderReceiver.class);
        intent.putExtra("text", TEXTS[id-1]);
        intent.putExtra("id", id);
        PendingIntent pi = PendingIntent.getBroadcast(context, 9000 + id, intent, PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE);
        alarm.setInexactRepeating(AlarmManager.RTC_WAKEUP, c.getTimeInMillis(), AlarmManager.INTERVAL_DAY, pi);
    }

    public static void cancel(Context context, int id) {
        AlarmManager alarm = (AlarmManager) context.getSystemService(Context.ALARM_SERVICE);
        if (alarm == null) return;
        Intent intent = new Intent(context, ReminderReceiver.class);
        PendingIntent pi = PendingIntent.getBroadcast(context, 9000 + id, intent, PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE);
        alarm.cancel(pi);
    }
}
