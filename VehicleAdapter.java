package com.khanh.baidoxe;

import android.content.Context;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.TextView;

import androidx.annotation.NonNull;
import androidx.recyclerview.widget.RecyclerView;

import java.util.List;

public class VehicleAdapter extends RecyclerView.Adapter<VehicleAdapter.VehicleViewHolder> {

    Context context;
    List<Vehicle> vehicleList;

    public VehicleAdapter(Context context, List<Vehicle> vehicleList) {
        this.context = context;
        this.vehicleList = vehicleList;
    }

    @NonNull
    @Override
    public VehicleViewHolder onCreateViewHolder(@NonNull ViewGroup parent, int viewType) {
        View view = LayoutInflater.from(context).inflate(R.layout.item_vehicle, parent, false);
        return new VehicleViewHolder(view);
    }

    @Override
    public void onBindViewHolder(@NonNull VehicleViewHolder holder, int position) {
        Vehicle v = vehicleList.get(position);

        holder.txtPlate.setText("Biển số: " + v.plate);
        holder.txtDateIn.setText("Giờ vào: " + v.dateIn);
        holder.txtDateOut.setText("Giờ ra: " + (v.dateOut == null ? "Chưa ra" : v.dateOut));
        holder.txtStatus.setText("Trạng thái: " + (v.status == 1 ? "Còn trong bãi" : "Đã ra"));
        holder.txtFee.setText("Phí giữ xe: " + (v.fee > 0 ? v.fee + " VNĐ" : "Miễn phí dưới 30 phút"));

        holder.itemView.setOnClickListener(view -> {
            if (v.status == 0 && v.dateOut != null) {
                android.widget.Toast.makeText(context,
                        "Xe " + v.plate + " phí giữ xe: " + v.fee + " VNĐ",
                        android.widget.Toast.LENGTH_LONG).show();
            } else {
                android.widget.Toast.makeText(context,
                        "Xe chưa ra, chưa tính phí.",
                        android.widget.Toast.LENGTH_SHORT).show();
            }
        });
    }

    @Override
    public int getItemCount() {
        return vehicleList.size();
    }

    static class VehicleViewHolder extends RecyclerView.ViewHolder {
        TextView txtPlate, txtDateIn, txtDateOut, txtStatus, txtFee;

        public VehicleViewHolder(@NonNull View itemView) {
            super(itemView);
            txtPlate = itemView.findViewById(R.id.txtPlate);
            txtDateIn = itemView.findViewById(R.id.txtDateIn);
            txtDateOut = itemView.findViewById(R.id.txtDateOut);
            txtStatus = itemView.findViewById(R.id.txtStatus);
            txtFee = itemView.findViewById(R.id.txtFee);
        }
    }
}
