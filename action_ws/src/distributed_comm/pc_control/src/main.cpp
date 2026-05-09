/**
 * @file    main.cpp
 * @brief   PC QT5 UI entry point: init ROS, create MainWindow, enter QT event loop
 *  作者: Qi Xiao\n *  邮箱: 2408128687@qq.com\n */
//  作者: Qi Xiao
//  邮箱: 2408128687@qq.com

#include <QApplication>
#include "main_window.h"

int main(int argc, char** argv) {
    QApplication app(argc, argv);
    app.setApplicationName("Jetson PC Control");
    app.setApplicationVersion("1.0.0");

    MainWindow window(argc, argv);
    window.show();

    return app.exec();
}
