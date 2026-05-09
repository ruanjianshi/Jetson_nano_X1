/**
 * @file    main_window.cpp
 * @brief   PC QT5 UI: command panel + telemetry display + log console
 * @details Uses QTimer to call ros::spinOnce(), connects to ROS master on Jetson.
 *          Commands sent as JSON via /pc/command, telemetry received from
 *          /jetson/telemetry and displayed in real time.
 *  作者: Qi Xiao\n *  邮箱: 2408128687@qq.com\n */
//  作者: Qi Xiao
//  邮箱: 2408128687@qq.com

#include "main_window.h"
#include <QVBoxLayout>
#include <QHBoxLayout>
#include <QGridLayout>
#include <QFont>
#include <QFrame>
#include <QDateTime>

// -------------------------------------------------------------------
// Constructor
// -------------------------------------------------------------------
MainWindow::MainWindow(int argc, char** argv, QWidget* parent)
    : QMainWindow(parent)
{
    setWindowTitle("Jetson PC Control  —  Qi Xiao");
    resize(800, 580);

    setupUI();
    setupROS(argc, argv);

    ros_timer_ = new QTimer(this);
    connect(ros_timer_, &QTimer::timeout, this, &MainWindow::rosSpin);
    ros_timer_->start(50);   // 20 Hz spin
}

MainWindow::~MainWindow() {
    if (ros::isStarted()) {
        ros::shutdown();
        ros::waitForShutdown();
    }
}

// -------------------------------------------------------------------
// UI Construction
// -------------------------------------------------------------------
void MainWindow::setupUI() {
    QWidget* central = new QWidget(this);
    setCentralWidget(central);
    QVBoxLayout* mainLayout = new QVBoxLayout(central);

    // ---- Connection status bar ----
    QHBoxLayout* connRow = new QHBoxLayout();
    connRow->addWidget(new QLabel("ROS Status:"));
    label_conn_status_ = new QLabel("DISCONNECTED");
    label_conn_status_->setStyleSheet("QLabel { color: red; font-weight: bold; }");
    connRow->addWidget(label_conn_status_);
    connRow->addStretch();
    mainLayout->addLayout(connRow);

    // ---- Split: Controls | Telemetry ----
    QHBoxLayout* splitRow = new QHBoxLayout();

    // --- Controls Panel ---
    QGroupBox* ctrlGroup = new QGroupBox("Commands");
    QVBoxLayout* ctrlLayout = new QVBoxLayout(ctrlGroup);

    // LED
    QGroupBox* ledBox = new QGroupBox("LED");
    QHBoxLayout* ledRow = new QHBoxLayout(ledBox);
    btn_led_on_  = new QPushButton("ON");
    btn_led_off_ = new QPushButton("OFF");
    btn_led_on_->setStyleSheet("QPushButton { background-color: #4CAF50; color: white; }");
    btn_led_off_->setStyleSheet("QPushButton { background-color: #f44336; color: white; }");
    ledRow->addWidget(btn_led_on_);
    ledRow->addWidget(btn_led_off_);
    ctrlLayout->addWidget(ledBox);

    // Motor
    QGroupBox* motorBox = new QGroupBox("Motor Speed");
    QVBoxLayout* motorLayout = new QVBoxLayout(motorBox);
    slider_motor_ = new QSlider(Qt::Horizontal);
    slider_motor_->setRange(0, 100);
    slider_motor_->setValue(0);
    QHBoxLayout* motorValRow = new QHBoxLayout();
    motorValRow->addWidget(slider_motor_);
    label_motor_val_ = new QLabel("0");
    motorValRow->addWidget(label_motor_val_);
    QPushButton* btn_motor = new QPushButton("Set Motor");
    motorLayout->addLayout(motorValRow);
    motorLayout->addWidget(btn_motor);
    connect(slider_motor_, &QSlider::valueChanged, [this](int v){ label_motor_val_->setText(QString::number(v)); });
    connect(btn_motor, &QPushButton::clicked, this, &MainWindow::onMotorSet);
    ctrlLayout->addWidget(motorBox);

    // Servo
    QGroupBox* servoBox = new QGroupBox("Servo Angle");
    QHBoxLayout* servoRow = new QHBoxLayout(servoBox);
    spin_servo_ = new QSpinBox();
    spin_servo_->setRange(0, 180);
    spin_servo_->setValue(90);
    spin_servo_->setSuffix(" deg");
    btn_servo_set_ = new QPushButton("Set Servo");
    servoRow->addWidget(spin_servo_);
    servoRow->addWidget(btn_servo_set_);
    ctrlLayout->addWidget(servoBox);

    // Status request
    btn_status_ = new QPushButton("Request Telemetry");
    ctrlLayout->addWidget(btn_status_);

    ctrlLayout->addStretch();
    ctrlGroup->setFixedWidth(250);
    splitRow->addWidget(ctrlGroup);

    // --- Telemetry Panel ---
    QGroupBox* teleGroup = new QGroupBox("Jetson Telemetry");
    QGridLayout* teleGrid = new QGridLayout(teleGroup);

    auto makeTeleRow = [&](int row, const QString& label, QLabel*& value) {
        teleGrid->addWidget(new QLabel(label), row, 0);
        value = new QLabel("--");
        value->setStyleSheet("QLabel { font-weight: bold; font-size: 13px; }");
        teleGrid->addWidget(value, row, 1);
    };

    makeTeleRow(0, "CPU Temp:",    label_cpu_temp_);
    makeTeleRow(1, "CPU Usage:",   label_cpu_pct_);
    makeTeleRow(2, "Uptime:",      label_uptime_);
    makeTeleRow(3, "Memory:",      label_mem_);
    makeTeleRow(4, "LED:",         label_led_);
    makeTeleRow(5, "Motor:",       label_motor_);
    makeTeleRow(6, "Servo:",       label_servo_);

    teleGroup->setFixedWidth(250);
    splitRow->addWidget(teleGroup);

    mainLayout->addLayout(splitRow);

    // --- Log Console ---
    QGroupBox* logGroup = new QGroupBox("Log");
    QVBoxLayout* logLayout = new QVBoxLayout(logGroup);
    log_view_ = new QTextEdit();
    log_view_->setReadOnly(true);
    log_view_->setMaximumHeight(180);
    QFont mono("Courier New", 10);
    log_view_->setFont(mono);
    logLayout->addWidget(log_view_);
    mainLayout->addWidget(logGroup);

    // ---- Signal connections ----
    connect(btn_led_on_,  &QPushButton::clicked, this, &MainWindow::onLedOn);
    connect(btn_led_off_, &QPushButton::clicked, this, &MainWindow::onLedOff);
    connect(btn_servo_set_, &QPushButton::clicked, this, &MainWindow::onServoSet);
    connect(btn_status_, &QPushButton::clicked, this, &MainWindow::onStatusRequest);

    appendLog("QT UI initialized. Waiting for ROS connection...", QColor(100, 100, 100));
}

// -------------------------------------------------------------------
// ROS Setup
// -------------------------------------------------------------------
void MainWindow::setupROS(int argc, char** argv) {
    ros::init(argc, argv, "pc_control_ui",
              ros::init_options::NoSigintHandler);
    if (!ros::master::check()) {
        appendLog("ROS master not reachable!", Qt::red);
        return;
    }
    ros::NodeHandle nh;
    cmd_pub_  = nh.advertise<std_msgs::String>("/pc/command", 10);
    tele_sub_ = nh.subscribe("/jetson/telemetry", 10,
                             &MainWindow::telemetryCallback, this, ros::TransportHints().tcpNoDelay());
    appendLog("Connected to ROS master", QColor(0, 128, 0));
}

void MainWindow::rosSpin() {
    if (ros::ok()) {
        ros::spinOnce();
    }
    bool connected = ros::master::check();
    label_conn_status_->setText(connected ? "CONNECTED" : "DISCONNECTED");
    label_conn_status_->setStyleSheet(connected
        ? "QLabel { color: green; font-weight: bold; }"
        : "QLabel { color: red; font-weight: bold; }");
}

// -------------------------------------------------------------------
// Command Handlers
// -------------------------------------------------------------------
void MainWindow::sendCommand(const std::string& json) {
    if (!ros::master::check()) {
        appendLog("Cannot send: ROS master not connected", Qt::red);
        return;
    }
    std_msgs::String msg;
    msg.data = json;
    cmd_pub_.publish(msg);
    appendLog("Sent: " + QString::fromStdString(json), QColor(0, 100, 200));
}

void MainWindow::onLedOn()        { sendCommand("{\"cmd\":\"led_on\"}"); }
void MainWindow::onLedOff()       { sendCommand("{\"cmd\":\"led_off\"}"); }

void MainWindow::onMotorSet() {
    int speed = slider_motor_->value();
    sendCommand("{\"cmd\":\"motor\",\"speed\":" + std::to_string(speed) + "}");
}

void MainWindow::onServoSet() {
    int angle = spin_servo_->value();
    sendCommand("{\"cmd\":\"servo\",\"angle\":" + std::to_string(angle) + "}");
}

void MainWindow::onStatusRequest() { sendCommand("{\"cmd\":\"status\"}"); }

// -------------------------------------------------------------------
// Telemetry Callback
// -------------------------------------------------------------------
void MainWindow::telemetryCallback(const std_msgs::String::ConstPtr& msg) {
    Json::Value root;
    Json::Reader reader;
    if (!reader.parse(msg->data, root)) return;

    label_cpu_temp_->setText(QString::number(root.get("cpu_temp", -1).asFloat(), 'f', 1) + " C");
    label_cpu_pct_->setText(QString::number(root.get("cpu_percent", -1).asInt()) + " %");
    int uptime = root.get("uptime", 0).asInt();
    label_uptime_->setText(QString("%1h %2m %3s").arg(uptime/3600).arg((uptime%3600)/60).arg(uptime%60));

    float used  = root.get("mem_used", 0).asFloat();
    float total = root.get("mem_total", 0).asFloat();
    label_mem_->setText(QString("%1 / %2 GB").arg(used, 0, 'f', 1).arg(total, 0, 'f', 1));

    label_led_->setText(root.get("led", 0).asInt() ? "ON" : "OFF");
    label_motor_->setText(QString::number(root.get("motor", 0).asInt()));
    label_servo_->setText(QString::number(root.get("servo", 90).asInt()) + " deg");
}

// -------------------------------------------------------------------
// Log Utility
// -------------------------------------------------------------------
void MainWindow::appendLog(const QString& text, const QColor& color) {
    QString ts = QDateTime::currentDateTime().toString("hh:mm:ss");
    log_view_->setTextColor(color);
    log_view_->append("[" + ts + "] " + text);
    // Auto-scroll to bottom
    QTextCursor c = log_view_->textCursor();
    c.movePosition(QTextCursor::End);
    log_view_->setTextCursor(c);
}
