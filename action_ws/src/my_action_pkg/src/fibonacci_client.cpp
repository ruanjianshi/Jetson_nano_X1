#include <ros/ros.h>
#include <actionlib/client/simple_action_client.h>
#include <my_action_pkg/FibonacciAction.h>
#include <sstream>
#include <vector>

// 辅助函数：将 vector<int> 转换为字符串
std::string vec_to_str(const std::vector<int>& vec) {
    std::stringstream ss;
    ss << "[";
    for (size_t i = 0; i < vec.size(); ++i) {
        if (i != 0) ss << ", ";
        ss << vec[i];
    }
    ss << "]";
    return ss.str();
}

void feedbackCallback(const my_action_pkg::FibonacciFeedbackConstPtr& feedback) {
    ROS_INFO_STREAM("Feedback: " << vec_to_str(feedback->partial_sequence));
}

int main(int argc, char** argv) {
    ros::init(argc, argv, "fibonacci_client");
    ROS_INFO("Node name: %s", ros::this_node::getName().c_str());

    // 从私有命名空间读取参数，默认10
    int order;
    ros::param::param<int>("~order", order, 10);
    ROS_INFO_STREAM("Using order from param: " << order);

    // 创建 Action 客户端
    actionlib::SimpleActionClient<my_action_pkg::FibonacciAction> ac("fibonacci", true);
    ROS_INFO("Waiting for action server...");
    ac.waitForServer();

    // 构造目标
    my_action_pkg::FibonacciGoal goal;
    goal.order = order;
    ROS_INFO_STREAM("Sending goal: order=" << goal.order);

    // 发送目标，指定反馈回调
    ac.sendGoal(goal, NULL, NULL, boost::bind(&feedbackCallback, _1));

    // 等待结果，超时10秒
    bool finished = ac.waitForResult(ros::Duration(10.0));
    if (finished) {
        actionlib::SimpleClientGoalState state = ac.getState();
        ROS_INFO("Action finished: %s", state.toString().c_str());
        my_action_pkg::FibonacciResultConstPtr result = ac.getResult();
        if (result) {
            ROS_INFO_STREAM("Result: " << vec_to_str(result->sequence));
        }
    } else {
        ROS_WARN("Action did not finish before timeout");
    }

    return 0;
}