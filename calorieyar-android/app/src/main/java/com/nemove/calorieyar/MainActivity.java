package com.nemove.calorieyar;

import android.Manifest;
import android.app.AlertDialog;
import android.content.pm.PackageManager;
import android.graphics.Color;
import android.graphics.Typeface;
import android.graphics.drawable.GradientDrawable;
import android.os.Build;
import android.os.Bundle;
import android.text.Editable;
import android.text.TextWatcher;
import android.view.Gravity;
import android.view.View;
import android.widget.Button;
import android.widget.EditText;
import android.widget.HorizontalScrollView;
import android.widget.LinearLayout;
import android.widget.ProgressBar;
import android.widget.ScrollView;
import android.widget.Spinner;
import android.widget.ArrayAdapter;
import android.widget.Switch;
import android.widget.TextView;
import android.widget.Toast;

import org.json.JSONArray;
import org.json.JSONObject;

import java.util.List;
import java.util.Locale;

public final class MainActivity extends android.app.Activity {
    private static final int BRAND = Color.rgb(47,109,90);
    private static final int BG = Color.rgb(247,248,246);
    private static final int TEXT = Color.rgb(24,32,29);
    private static final int MUTED = Color.rgb(102,113,108);
    private static final int BORDER = Color.rgb(226,231,228);

    private DataStore store;
    private LinearLayout root;
    private LinearLayout content;
    private int currentTab = 0;

    @Override protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        getWindow().setStatusBarColor(BG);
        getWindow().setNavigationBarColor(Color.WHITE);
        store = new DataStore(this);
        ReminderScheduler.applyAll(this);
        askNotificationPermission();
        buildShell();
        showHome();
    }

    private void askNotificationPermission() {
        if (Build.VERSION.SDK_INT >= 33 && checkSelfPermission(Manifest.permission.POST_NOTIFICATIONS) != PackageManager.PERMISSION_GRANTED) {
            requestPermissions(new String[]{Manifest.permission.POST_NOTIFICATIONS}, 55);
        }
    }

    private void buildShell() {
        root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setBackgroundColor(BG);
        root.setLayoutDirection(View.LAYOUT_DIRECTION_RTL);

        LinearLayout header = new LinearLayout(this);
        header.setOrientation(LinearLayout.HORIZONTAL);
        header.setGravity(Gravity.CENTER_VERTICAL);
        header.setPadding(dp(20), dp(16), dp(20), dp(10));
        TextView title = text("کالری‌یار", 24, TEXT, true);
        TextView badge = text("نسخه ۱", 12, BRAND, true);
        badge.setPadding(dp(10),dp(5),dp(10),dp(5));
        badge.setBackground(round(Color.rgb(232,241,237), 20, Color.TRANSPARENT));
        header.addView(title, new LinearLayout.LayoutParams(0, dp(48), 1));
        header.addView(badge);
        root.addView(header);

        content = new LinearLayout(this);
        content.setOrientation(LinearLayout.VERTICAL);
        root.addView(content, new LinearLayout.LayoutParams(-1, 0, 1));
        root.addView(bottomNav());
        setContentView(root);
    }

    private View bottomNav() {
        LinearLayout nav = new LinearLayout(this);
        nav.setOrientation(LinearLayout.HORIZONTAL);
        nav.setGravity(Gravity.CENTER);
        nav.setPadding(dp(8), dp(8), dp(8), dp(10));
        nav.setBackgroundColor(Color.WHITE);
        String[] labels = {"خانه", "غذا", "فعالیت", "تاریخچه", "تنظیمات"};
        for (int i=0;i<labels.length;i++) {
            final int idx=i;
            Button b = new Button(this);
            b.setText(labels[i]);
            b.setTextSize(12);
            b.setAllCaps(false);
            b.setTextColor(i==0 ? BRAND : MUTED);
            b.setBackgroundColor(Color.TRANSPARENT);
            b.setPadding(2,0,2,0);
            b.setOnClickListener(v -> {
                currentTab=idx;
                switch (idx) {
                    case 0 -> showHome();
                    case 1 -> showFood();
                    case 2 -> showActivity();
                    case 3 -> showHistory();
                    default -> showSettings();
                }
                refreshNav((LinearLayout) b.getParent());
            });
            nav.addView(b, new LinearLayout.LayoutParams(0, dp(52), 1));
        }
        return nav;
    }

    private void refreshNav(LinearLayout nav) {
        for (int i=0;i<nav.getChildCount();i++) ((Button)nav.getChildAt(i)).setTextColor(i==currentTab ? BRAND : MUTED);
    }

    private ScrollView page() {
        ScrollView s = new ScrollView(this);
        s.setFillViewport(true);
        s.setClipToPadding(false);
        s.setPadding(dp(16),0,dp(16),dp(18));
        return s;
    }

    private void showHome() {
        currentTab=0;
        content.removeAllViews();
        ScrollView scroll=page();
        LinearLayout box=column();
        scroll.addView(box);
        DataStore.Totals t=store.totalsToday();
        int target=store.getTarget();
        int remaining=NutritionMath.remaining(target,t.eaten,t.burned);

        TextView hello=text("امروزت چطور پیش می‌رود؟",18,TEXT,true);
        hello.setPadding(0,dp(8),0,dp(12));
        box.addView(hello);

        LinearLayout hero=card();
        TextView remain=text(formatNumber(remaining)+" کالری",34,TEXT,true);
        remain.setGravity(Gravity.CENTER);
        TextView sub=text("باقی‌مانده از هدف روزانه",14,MUTED,false); sub.setGravity(Gravity.CENTER);
        ProgressBar progress=new ProgressBar(this,null,android.R.attr.progressBarStyleHorizontal);
        progress.setMax(Math.max(1,target)); progress.setProgress(Math.min(target,t.eaten)); progress.setProgressTintList(android.content.res.ColorStateList.valueOf(BRAND));
        TextView status=text(formatNumber(t.eaten)+" مصرف  •  "+formatNumber(t.burned)+" فعالیت  •  هدف "+formatNumber(target),13,MUTED,false); status.setGravity(Gravity.CENTER);
        hero.addView(remain); hero.addView(sub); hero.addView(space(12)); hero.addView(progress,new LinearLayout.LayoutParams(-1,dp(9))); hero.addView(space(10)); hero.addView(status);
        box.addView(hero);

        TextView macroTitle=text("درشت‌مغذی‌های امروز",17,TEXT,true); macroTitle.setPadding(0,dp(22),0,dp(10)); box.addView(macroTitle);
        LinearLayout macros=new LinearLayout(this); macros.setOrientation(LinearLayout.HORIZONTAL); macros.setWeightSum(3);
        macros.addView(metric("پروتئین", String.format(Locale.US,"%.0f g",t.protein)), new LinearLayout.LayoutParams(0,-2,1));
        macros.addView(metric("کربوهیدرات", String.format(Locale.US,"%.0f g",t.carbs)), new LinearLayout.LayoutParams(0,-2,1));
        macros.addView(metric("چربی", String.format(Locale.US,"%.0f g",t.fat)), new LinearLayout.LayoutParams(0,-2,1));
        box.addView(macros);

        TextView quick=text("ثبت سریع",17,TEXT,true); quick.setPadding(0,dp(22),0,dp(10)); box.addView(quick);
        LinearLayout actions=new LinearLayout(this); actions.setOrientation(LinearLayout.HORIZONTAL);
        Button food=primary("+ ثبت غذا"); food.setOnClickListener(v->showFood());
        Button act=secondary("+ ثبت فعالیت"); act.setOnClickListener(v->showActivity());
        actions.addView(food,new LinearLayout.LayoutParams(0,dp(52),1));
        actions.addView(spaceH(8));
        actions.addView(act,new LinearLayout.LayoutParams(0,dp(52),1));
        box.addView(actions);

        LinearLayout ai=card(); ai.setPadding(dp(16),dp(15),dp(16),dp(15));
        TextView aiT=text("دستیار هوشمند",16,TEXT,true);
        TextView aiS=text("معماری این بخش برای اتصال MCP / ChatGPT آماده است. در V1 محاسبات اصلی مستقل و آفلاین انجام می‌شود.",13,MUTED,false);
        ai.addView(aiT); ai.addView(space(5)); ai.addView(aiS);
        LinearLayout.LayoutParams ap=new LinearLayout.LayoutParams(-1,-2); ap.topMargin=dp(18); box.addView(ai,ap);

        content.addView(scroll,new LinearLayout.LayoutParams(-1,-1));
    }

    private void showFood() {
        currentTab=1; content.removeAllViews();
        LinearLayout shell=column(); shell.setPadding(dp(16),0,dp(16),0);
        TextView h=text("چی خوردی؟",22,TEXT,true); h.setPadding(0,dp(8),0,dp(8)); shell.addView(h);
        TextView tip=text("غذا را جستجو کن و مقدارش را انتخاب کن. واحدها برای مصرف روزمره ایرانی ساده شده‌اند.",13,MUTED,false); shell.addView(tip);
        EditText search=input("مثلاً قورمه‌سبزی، برنج، تخم‌مرغ..."); LinearLayout.LayoutParams sp=new LinearLayout.LayoutParams(-1,dp(54)); sp.topMargin=dp(14); shell.addView(search,sp);
        ScrollView listScroll=new ScrollView(this); LinearLayout list=column(); list.setPadding(0,dp(8),0,dp(18)); listScroll.addView(list); shell.addView(listScroll,new LinearLayout.LayoutParams(-1,0,1));
        renderFoods(list,FoodDatabase.FOODS);
        search.addTextChangedListener(new TextWatcher(){public void beforeTextChanged(CharSequence s,int st,int c,int a){} public void onTextChanged(CharSequence s,int st,int b,int c){renderFoods(list,FoodDatabase.search(s.toString()));} public void afterTextChanged(Editable e){}});
        content.addView(shell,new LinearLayout.LayoutParams(-1,-1));
    }

    private void renderFoods(LinearLayout list, List<FoodItem> foods) {
        list.removeAllViews();
        for (FoodItem f:foods) {
            LinearLayout row=card(); row.setOrientation(LinearLayout.HORIZONTAL); row.setGravity(Gravity.CENTER_VERTICAL); row.setPadding(dp(14),dp(12),dp(14),dp(12));
            LinearLayout info=column(); TextView name=text(f.name,15,TEXT,true); TextView unit=text(f.unit+" • "+formatNumber((int)f.calories)+" kcal",12,MUTED,false); info.addView(name); info.addView(unit);
            TextView plus=text("+",26,BRAND,true); plus.setGravity(Gravity.CENTER); plus.setBackground(round(Color.rgb(232,241,237),18,Color.TRANSPARENT));
            row.addView(info,new LinearLayout.LayoutParams(0,-2,1)); row.addView(plus,new LinearLayout.LayoutParams(dp(42),dp(42)));
            row.setOnClickListener(v->foodDialog(f));
            LinearLayout.LayoutParams rp=new LinearLayout.LayoutParams(-1,-2); rp.bottomMargin=dp(8); list.addView(row,rp);
        }
        if (foods.isEmpty()) { TextView empty=text("موردی پیدا نشد.",14,MUTED,false); empty.setGravity(Gravity.CENTER); empty.setPadding(0,dp(40),0,0); list.addView(empty); }
    }

    private void foodDialog(FoodItem f) {
        LinearLayout box=column(); box.setPadding(dp(18),dp(8),dp(18),0);
        TextView unit=text("واحد: "+f.unit,13,MUTED,false); box.addView(unit);
        EditText amount=input("مقدار، مثلاً 1 یا 1.5"); amount.setInputType(android.text.InputType.TYPE_CLASS_NUMBER|android.text.InputType.TYPE_NUMBER_FLAG_DECIMAL); amount.setText("1"); box.addView(amount,new LinearLayout.LayoutParams(-1,dp(52)));
        Spinner meal=new Spinner(this); String[] meals={"صبحانه","ناهار","میان‌وعده","شام"}; meal.setAdapter(new ArrayAdapter<>(this,android.R.layout.simple_spinner_dropdown_item,meals)); LinearLayout.LayoutParams mp=new LinearLayout.LayoutParams(-1,dp(56)); mp.topMargin=dp(8); box.addView(meal,mp);
        new AlertDialog.Builder(this).setTitle(f.name).setView(box).setNegativeButton("انصراف",null).setPositiveButton("ثبت",(d,w)->{
            try { double a=Double.parseDouble(amount.getText().toString().trim()); if(a<=0) throw new Exception(); store.addFood(f,a,(String)meal.getSelectedItem()); Toast.makeText(this,"ثبت شد",Toast.LENGTH_SHORT).show(); showHome(); }
            catch(Exception e){ Toast.makeText(this,"مقدار معتبر وارد کن",Toast.LENGTH_SHORT).show(); }
        }).show();
    }

    private void showActivity() {
        currentTab=2; content.removeAllViews();
        ScrollView scroll=page(); LinearLayout box=column(); scroll.addView(box);
        TextView h=text("فعالیت امروز",22,TEXT,true); h.setPadding(0,dp(8),0,dp(5)); box.addView(h);
        TextView s=text("کالری فعالیت با فرمول MET و وزن ثبت‌شده در تنظیمات محاسبه می‌شود.",13,MUTED,false); box.addView(s);
        for(ActivityType a:FoodDatabase.ACTIVITIES){
            LinearLayout row=card(); row.setOrientation(LinearLayout.HORIZONTAL); row.setGravity(Gravity.CENTER_VERTICAL); row.setPadding(dp(14),dp(12),dp(14),dp(12));
            TextView n=text(a.name,15,TEXT,true); TextView met=text(String.format(Locale.US,"MET %.1f",a.met),12,MUTED,false);
            LinearLayout inf=column(); inf.addView(n); inf.addView(met); TextView plus=text("+",26,BRAND,true); plus.setGravity(Gravity.CENTER); plus.setBackground(round(Color.rgb(232,241,237),18,Color.TRANSPARENT));
            row.addView(inf,new LinearLayout.LayoutParams(0,-2,1)); row.addView(plus,new LinearLayout.LayoutParams(dp(42),dp(42))); row.setOnClickListener(v->activityDialog(a));
            LinearLayout.LayoutParams rp=new LinearLayout.LayoutParams(-1,-2); rp.topMargin=dp(8); box.addView(row,rp);
        }
        content.addView(scroll,new LinearLayout.LayoutParams(-1,-1));
    }

    private void activityDialog(ActivityType a) {
        EditText mins=input("مدت به دقیقه"); mins.setInputType(android.text.InputType.TYPE_CLASS_NUMBER); mins.setText("30"); mins.setPadding(dp(14),0,dp(14),0);
        new AlertDialog.Builder(this).setTitle(a.name).setMessage("وزن فعلی: "+String.format(Locale.US,"%.0f",store.getWeight())+" کیلوگرم").setView(mins).setNegativeButton("انصراف",null).setPositiveButton("ثبت",(d,w)->{
            try { int m=Integer.parseInt(mins.getText().toString().trim()); if(m<=0||m>600) throw new Exception(); store.addActivity(a,m,store.getWeight()); Toast.makeText(this,"فعالیت ثبت شد",Toast.LENGTH_SHORT).show(); showHome(); }
            catch(Exception e){Toast.makeText(this,"مدت معتبر وارد کن",Toast.LENGTH_SHORT).show();}
        }).show();
    }

    private void showHistory() {
        currentTab=3; content.removeAllViews();
        ScrollView scroll=page(); LinearLayout box=column(); scroll.addView(box);
        TextView h=text("تاریخچه امروز",22,TEXT,true); h.setPadding(0,dp(8),0,dp(8)); box.addView(h);
        JSONArray arr=store.logs(); int count=0;
        for(int i=arr.length()-1;i>=0;i--){
            JSONObject o=arr.optJSONObject(i); if(o==null||!DataStore.today().equals(o.optString("date"))) continue; count++;
            LinearLayout row=card(); row.setOrientation(LinearLayout.HORIZONTAL); row.setGravity(Gravity.CENTER_VERTICAL); row.setPadding(dp(14),dp(12),dp(14),dp(12));
            LinearLayout inf=column(); String type=o.optString("type"); TextView n=text(o.optString("name"),15,TEXT,true); TextView m=text(o.optString("meal")+" • "+o.optInt("cal")+("activity".equals(type)?" kcal مصرف":" kcal"),12,MUTED,false); inf.addView(n); inf.addView(m);
            Button del=secondary("حذف"); del.setTextSize(11); long id=o.optLong("id"); del.setOnClickListener(v->{store.delete(id);showHistory();});
            row.addView(inf,new LinearLayout.LayoutParams(0,-2,1)); row.addView(del,new LinearLayout.LayoutParams(dp(70),dp(40)));
            LinearLayout.LayoutParams rp=new LinearLayout.LayoutParams(-1,-2); rp.bottomMargin=dp(8); box.addView(row,rp);
        }
        if(count==0){TextView empty=text("هنوز چیزی برای امروز ثبت نشده.",14,MUTED,false); empty.setGravity(Gravity.CENTER); empty.setPadding(0,dp(50),0,0); box.addView(empty);}
        content.addView(scroll,new LinearLayout.LayoutParams(-1,-1));
    }

    private void showSettings() {
        currentTab=4; content.removeAllViews();
        ScrollView scroll=page(); LinearLayout box=column(); scroll.addView(box);
        TextView h=text("تنظیمات",22,TEXT,true); h.setPadding(0,dp(8),0,dp(12)); box.addView(h);
        TextView goalTitle=text("هدف و مشخصات",17,TEXT,true); box.addView(goalTitle);
        LinearLayout goal=card();
        EditText target=input("هدف کالری روزانه"); target.setInputType(android.text.InputType.TYPE_CLASS_NUMBER); target.setText(String.valueOf(store.getTarget()));
        EditText weight=input("وزن (kg)"); weight.setInputType(android.text.InputType.TYPE_CLASS_NUMBER|android.text.InputType.TYPE_NUMBER_FLAG_DECIMAL); weight.setText(String.format(Locale.US,"%.0f",store.getWeight()));
        goal.addView(target,new LinearLayout.LayoutParams(-1,dp(52))); LinearLayout.LayoutParams wp=new LinearLayout.LayoutParams(-1,dp(52)); wp.topMargin=dp(8); goal.addView(weight,wp);
        Button save=primary("ذخیره مشخصات"); LinearLayout.LayoutParams svp=new LinearLayout.LayoutParams(-1,dp(50)); svp.topMargin=dp(10); goal.addView(save,svp);
        save.setOnClickListener(v->{try{int t=Integer.parseInt(target.getText().toString());double w=Double.parseDouble(weight.getText().toString()); if(t<1200||t>6000||w<30||w>300)throw new Exception();store.setTarget(t);store.setWeight(w);Toast.makeText(this,"ذخیره شد",Toast.LENGTH_SHORT).show();}catch(Exception e){Toast.makeText(this,"مقادیر را بررسی کن",Toast.LENGTH_SHORT).show();}});
        LinearLayout.LayoutParams gp=new LinearLayout.LayoutParams(-1,-2); gp.topMargin=dp(8); box.addView(goal,gp);

        TextView rt=text("یادآوری‌ها",17,TEXT,true); rt.setPadding(0,dp(22),0,dp(8)); box.addView(rt);
        String[] names={"صبحانه • حدود 08:30","ناهار • حدود 13:30","بررسی عصر • حدود 18:00","تکمیل روز • حدود 22:00"};
        for(int i=1;i<=4;i++){ final int id=i; LinearLayout row=card(); row.setOrientation(LinearLayout.HORIZONTAL); row.setGravity(Gravity.CENTER_VERTICAL); row.setPadding(dp(14),dp(8),dp(14),dp(8)); TextView tx=text(names[i-1],14,TEXT,false); Switch sw=new Switch(this); sw.setChecked(store.getReminder(id)); sw.setOnCheckedChangeListener((b,on)->{store.setReminder(id,on); if(on) ReminderScheduler.schedule(this,id); else ReminderScheduler.cancel(this,id);}); row.addView(tx,new LinearLayout.LayoutParams(0,-2,1)); row.addView(sw); LinearLayout.LayoutParams rp=new LinearLayout.LayoutParams(-1,-2); rp.bottomMargin=dp(8); box.addView(row,rp); }

        LinearLayout note=card(); TextView nt=text("حریم خصوصی V1",15,TEXT,true); TextView ns=text("اطلاعات این نسخه روی خود دستگاه ذخیره می‌شود و برای محاسبه کالری نیازی به ارسال داده به سرویس خارجی نیست.",13,MUTED,false); note.addView(nt);note.addView(space(5));note.addView(ns); LinearLayout.LayoutParams np=new LinearLayout.LayoutParams(-1,-2);np.topMargin=dp(12);box.addView(note,np);
        content.addView(scroll,new LinearLayout.LayoutParams(-1,-1));
    }

    private LinearLayout column(){LinearLayout l=new LinearLayout(this);l.setOrientation(LinearLayout.VERTICAL);l.setLayoutDirection(View.LAYOUT_DIRECTION_RTL);return l;}
    private LinearLayout card(){LinearLayout l=column();l.setPadding(dp(16),dp(16),dp(16),dp(16));l.setBackground(round(Color.WHITE,18,BORDER));return l;}
    private View metric(String label,String value){
        LinearLayout holder=new LinearLayout(this);
        holder.setPadding(dp(3),0,dp(3),0);
        LinearLayout box=card();
        box.setGravity(Gravity.CENTER);
        TextView v=text(value,20,TEXT,true); v.setGravity(Gravity.CENTER);
        TextView l=text(label,11,MUTED,false); l.setGravity(Gravity.CENTER);
        box.addView(v); box.addView(l);
        holder.addView(box,new LinearLayout.LayoutParams(-1,-2));
        return holder;
    }

    private TextView text(String s,int sp,int color,boolean bold){TextView t=new TextView(this);t.setText(s);t.setTextSize(sp);t.setTextColor(color);t.setGravity(Gravity.RIGHT|Gravity.CENTER_VERTICAL);t.setLineSpacing(0,1.1f);if(bold)t.setTypeface(Typeface.DEFAULT,Typeface.BOLD);return t;}
    private EditText input(String hint){EditText e=new EditText(this);e.setHint(hint);e.setTextSize(14);e.setTextColor(TEXT);e.setHintTextColor(Color.rgb(150,158,154));e.setSingleLine(true);e.setGravity(Gravity.RIGHT|Gravity.CENTER_VERTICAL);e.setPadding(dp(14),0,dp(14),0);e.setBackground(round(Color.WHITE,14,BORDER));return e;}
    private Button primary(String s){Button b=new Button(this);b.setText(s);b.setAllCaps(false);b.setTextColor(Color.WHITE);b.setTextSize(14);b.setTypeface(Typeface.DEFAULT,Typeface.BOLD);b.setBackground(round(BRAND,14,Color.TRANSPARENT));return b;}
    private Button secondary(String s){Button b=new Button(this);b.setText(s);b.setAllCaps(false);b.setTextColor(BRAND);b.setTextSize(14);b.setTypeface(Typeface.DEFAULT,Typeface.BOLD);b.setBackground(round(Color.WHITE,14,BORDER));return b;}
    private View space(int h){View v=new View(this);v.setLayoutParams(new LinearLayout.LayoutParams(1,dp(h)));return v;}
    private View spaceH(int w){View v=new View(this);v.setLayoutParams(new LinearLayout.LayoutParams(dp(w),1));return v;}
    private GradientDrawable round(int color,int radius,int stroke){GradientDrawable g=new GradientDrawable();g.setColor(color);g.setCornerRadius(dp(radius));if(stroke!=Color.TRANSPARENT)g.setStroke(dp(1),stroke);return g;}
    private int dp(int v){return Math.round(v*getResources().getDisplayMetrics().density);}
    private String formatNumber(int n){return String.format(Locale.US,"%,d",n);}
}
