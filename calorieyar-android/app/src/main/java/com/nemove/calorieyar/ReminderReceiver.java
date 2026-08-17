package com.nemove.calorieyar;

import android.app.NotificationChannel;
import android.app.NotificationManager;
import android.app.PendingIntent;
import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.os.Build;

public final class ReminderReceiver extends BroadcastReceiver {
    @Override public void onReceive(Context context, Intent intent) {
        NotificationManager nm = (NotificationManager) context.getSystemService(Context.NOTIFICATION_SERVICE);
        if (nm == null) return;
        String channelId = "daily_reminders";
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            NotificationChannel channel = new NotificationChannel(channelId, "یادآوری‌های روزانه", NotificationManager.IMPORTANCE_DEFAULT);
            nm.createNotificationChannel(channel);
        }
        Intent open = new Intent(context, MainActivity.class);
        PendingIntent pi = PendingIntent.getActivity(context, 0, open, PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE);
        android.app.Notification.Builder b = Build.VERSION.SDK_INT >= Build.VERSION_CODES.O
            ? new android.app.Notification.Builder(context, channelId)
            : new android.app.Notification.Builder(context);
        b.setSmallIcon(com.nemove.calorieyar.R.drawable.ic_launcher)
         .setContentTitle("کالری‌یار")
         .setContentText(intent.getStringExtra("text"))
         .setAutoCancel(true)
         .setContentIntent(pi);
        nm.notify(7000 + intent.getIntExtra("id", 0), b.build());
    }
}
