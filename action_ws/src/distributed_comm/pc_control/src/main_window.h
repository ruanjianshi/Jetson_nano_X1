/**
 * @file    main_window.h
 * @brief   PC QT5 UI: send commands to Jetson, display telemetry feedback
 *  作者: Qi Xiao\n *  邮箱: 2408128687@qq.com\n */
//  作者: Qi Xiao
//  邮箱: 2408128687@qq.com

#ifndef PC_CONTROL_MAIN_WINDOW_H
#define PC_CONTROL_MAIN_WINDOW_H

#include <QMainWindow>
#include <QTimer>
#include <QLabel>
#include <QPushButton>
#include <QSlider>
#include <QTextEdit>
#include <QSpinBox>
#include <QGroupBox>
#include "ros/ros.h"
#include "std_msgs/String.h"

class MainWindow : public QMainWindow {
    Q_OBJECT

public:
    explicit MainWindow(int argc, char** argv, QWidget* parent = nullptr);
    ~MainWindow();

private slots:
    void rosSpin();
    void onLedOn();
    void onLedOff();
    void onMotorSet();
    void onServoSet();
    void onStatusRequest();

private:
    void setupUI();
    void setupROS(int argc, char** argv);
    void sendCommand(const std::string& json);
    void telemetryCallback(const std_msgs::String::ConstPtr& msg);
    void appendLog(const QString& text, const QColor& color = Qt::black);

    // ROS
    ros::Publisher  cmd_pub_;
    ros::Subscriber tele_sub_;
    QTimer*         ros_timer_;

    // UI - Status
    QLabel*   label_conn_status_;
    QLabel*   label_cpu_temp_;
    QLabel*   label_cpu_pct_;
    QLabel*   label_uptime_;
    QLabel*   label_mem_;
    QLabel*   label_led_;
    QLabel*   label_motor_;
    QLabel*   label_servo_;

    // UI - Controls
    QPushButton* btn_led_on_;
    QPushButton* btn_led_off_;
    QSlider*     slider_motor_;
    QLabel*      label_motor_val_;
    QSpinBox*    spin_servo_;
    QPushButton* btn_servo_set_;
    QPushButton* btn_status_;

    // UI - Log
    QTextEdit* log_view_;
};

#endif // PC_CONTROL_MAIN_WINDOW_H
