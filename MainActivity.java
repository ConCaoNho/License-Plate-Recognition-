package com.khanh.baidoxe;

import androidx.appcompat.app.AppCompatActivity;
import androidx.recyclerview.widget.LinearLayoutManager;
import androidx.recyclerview.widget.RecyclerView;

import android.os.Bundle;
import android.os.Handler;
import android.widget.TextView;
import android.widget.Toast;

import com.android.volley.Request;
import com.android.volley.RequestQueue;
import com.android.volley.toolbox.JsonArrayRequest;
import com.android.volley.toolbox.Volley;

import org.json.JSONObject;

import java.text.SimpleDateFormat;
import java.util.ArrayList;
import java.util.Date;
import java.util.List;

public class MainActivity extends AppCompatActivity {

    TextView txtTotal;
    TextView txtSlotLeft;
    RecyclerView recyclerVehicles;

    VehicleAdapter adapter;
    List<Vehicle> vehicleList = new ArrayList<>();

    String API_URL = "http://192.168.1.223/getVehicles.php";

    Handler handler = new Handler();
    Runnable autoUpdateRunnable;

    private static final int MAX_SLOT = 10; // ✅ GIỚI HẠN SỐ CHỖ ĐỖ XE

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        txtTotal = findViewById(R.id.txtTotal);
        txtSlotLeft = findViewById(R.id.txtSlotLeft);
        recyclerVehicles = findViewById(R.id.recyclerVehicles);

        recyclerVehicles.setLayoutManager(new LinearLayoutManager(this));
        adapter = new VehicleAdapter(this, vehicleList);
        recyclerVehicles.setAdapter(adapter);

        // Gọi lần đầu khi mở app
        loadData();

        // Tự động load lại dữ liệu mỗi 5 giây
        autoUpdateRunnable = new Runnable() {
            @Override
            public void run() {
                loadData();
                handler.postDelayed(this, 5000); // 5000 ms = 5 giây
            }
        };
        handler.postDelayed(autoUpdateRunnable, 5000);
    }

    @Override
    protected void onDestroy() {
        super.onDestroy();
        handler.removeCallbacks(autoUpdateRunnable);
    }

    private void loadData() {
        RequestQueue queue = Volley.newRequestQueue(this);

        JsonArrayRequest request = new JsonArrayRequest(Request.Method.GET, API_URL, null,
                response -> {
                    vehicleList.clear();
                    int total = 0;

                    for (int i = 0; i < response.length(); i++) {
                        try {
                            JSONObject obj = response.getJSONObject(i);
                            String plate = obj.getString("number_plate");
                            String dateIn = obj.getString("date_in");
                            String dateOut = obj.isNull("date_out") ? null : obj.getString("date_out");
                            int status = obj.getInt("status");

                            int fee = 0;
                            if (status == 0 && dateOut != null) {
                                fee = calculateFee(dateIn, dateOut);
                            }

                            vehicleList.add(new Vehicle(plate, dateIn, dateOut, status, fee));

                            if (status == 1) total++;
                        } catch (Exception e) {
                            e.printStackTrace();
                        }
                    }

                    txtTotal.setText("Tổng số xe còn trong bãi: " + total);

                    int slotLeft = MAX_SLOT - total;
                    if (slotLeft < 0) slotLeft = 0;

                    txtSlotLeft.setText("Số chỗ trống còn lại: " + slotLeft);

                    if (total >= MAX_SLOT) {
                        Toast.makeText(this,
                                "⚠ Bãi xe đã đầy! Không cho xe vào nữa.",
                                Toast.LENGTH_LONG).show();
                    }

                    adapter.notifyDataSetChanged();
                },
                error -> {
                    error.printStackTrace();
                    Toast.makeText(this, "Lỗi mạng: " + error.toString(), Toast.LENGTH_LONG).show();
                }
        );

        queue.add(request);
    }

    private int calculateFee(String dateInStr, String dateOutStr) {
        try {
            SimpleDateFormat sdf = new SimpleDateFormat("yyyy-MM-dd HH:mm:ss");
            Date dateIn = sdf.parse(dateInStr);
            Date dateOut = sdf.parse(dateOutStr);

            long diffMillis = dateOut.getTime() - dateIn.getTime();
            long diffMinutes = diffMillis / (1000 * 60);

            if (diffMinutes <= 30) {
                return 0; // Miễn phí dưới 30 phút
            }

            long hours = diffMinutes / 60;
            if (diffMinutes % 60 > 0) {
                hours += 1; // Làm tròn lên nếu dư phút
            }

            if (hours == 0) hours = 1;

            return (int) (hours * 5000);
        } catch (Exception e) {
            e.printStackTrace();
        }
        return 0;
    }
}
