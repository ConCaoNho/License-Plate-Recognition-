package com.khanh.baidoxe;

public class Vehicle {
    public String plate;
    public String dateIn;
    public String dateOut;
    public int status;
    public int fee;

    public Vehicle(String plate, String dateIn, String dateOut, int status, int fee) {
        this.plate = plate;
        this.dateIn = dateIn;
        this.dateOut = dateOut;
        this.status = status;
        this.fee = fee;
    }
}
