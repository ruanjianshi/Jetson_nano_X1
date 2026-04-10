#include <ros/ros.h>
#include <actionlib/server/simple_action_server.h>
#include <my_action_pkg/FibonacciAction.h>  // 由 .action 生成的消息头文件

class FibonacciServer
{
protected:
    ros::NodeHandle nh_;
    actionlib::SimpleActionServer<my_action_pkg::FibonacciAction> as_;
    std::string action_name_;

    // 从参数服务器读取的配置
    double delay_;
    int default_order_;

public:
    FibonacciServer(const std::string& name) :
        as_(nh_, name, boost::bind(&FibonacciServer::execute, this, _1), false),
        action_name_(name)
    {
        // 从私有命名空间读取参数
        nh_.param("delay", delay_, 1.0);
        nh_.param("default_order", default_order_, 5);
        ROS_INFO_STREAM("Server config: delay=" << delay_ << ", default_order=" << default_order_);

        as_.start();
        ROS_INFO("Fibonacci action server started, node name: %s", ros::this_node::getName().c_str());
    }

    void execute(const my_action_pkg::FibonacciGoalConstPtr& goal)
    {
        int order = goal->order;
        if (order <= 0)
        {
            order = default_order_;
            ROS_WARN_STREAM("Goal order <= 0, using default order: " << order);
        }

        ROS_INFO_STREAM("Received goal with order: " << order);

        // 初始化斐波那契数列
        std::vector<int> fib_seq;
        fib_seq.push_back(0);
        fib_seq.push_back(1);

        my_action_pkg::FibonacciFeedback feedback;
        my_action_pkg::FibonacciResult result;

        for (int i = 1; i < order; ++i)
        {
            // 检查是否被取消
            if (as_.isPreemptRequested())
            {
                ROS_INFO("Preempted");
                as_.setPreempted();
                return;
            }

            // 计算下一个数
            fib_seq.push_back(fib_seq[i] + fib_seq[i-1]);

            // 发布反馈
            feedback.partial_sequence = fib_seq;
            as_.publishFeedback(feedback);

            // 模拟耗时操作
            ros::Duration(delay_).sleep();
        }

        // 成功结束
        result.sequence = fib_seq;
        as_.setSucceeded(result);
    }
};

int main(int argc, char** argv)
{
    ros::init(argc, argv, "fibonacci_server");
    FibonacciServer server("fibonacci");
    ros::spin();
    return 0;
}