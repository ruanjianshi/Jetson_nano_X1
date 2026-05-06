/*
 * ADP (Adaptive Dynamic Programming) Controller
 * ============================================
 *
 * ADP是一种自适应动态规划算法，通过在线学习来逼近最优控制策略。
 * 它由三个主要组件组成：
 *   1. Action Network (执行器网络) - 近似最优控制策略
 *   2. Critic Network (评价网络) - 近似最优价值函数
 *   3. Model Network (模型网络) - 近似系统动力学
 *
 * 作者: Jetson Nano
 * 日期: 2026-05-06
 */

#ifndef ADP_CONTROLLER_H
#define ADP_CONTROLLER_H

#include "balance_algorithm_base.h"
#include <vector>

namespace balance_control {

/*
 * 神经网络结构
 */
struct NeuralNetwork {
    std::vector<std::vector<double>> weights;  // 权重
    std::vector<double> biases;               // 偏置
    std::vector<double> inputs;               // 输入
    std::vector<double> outputs;              // 输出

    int input_size;
    int hidden_size;
    int output_size;

    NeuralNetwork() : input_size(0), hidden_size(0), output_size(0) {}

    NeuralNetwork(int input_dim, int hidden_dim, int output_dim)
        : input_size(input_dim), hidden_size(hidden_dim), output_size(output_dim) {
        initRandom();
    }

    void initRandom() {
        double limit = sqrt(6.0 / (input_size + hidden_size));
        weights.resize(2);
        weights[0].resize(hidden_size);
        weights[1].resize(output_size);

        for (auto& w : weights[0]) w = (rand() % 1000 - 500) / 500.0 * limit;
        for (auto& w : weights[1]) w = (rand() % 1000 - 500) / 500.0 * limit;

        biases.resize(hidden_size + output_size);
        for (auto& b : biases) b = 0.0;

        inputs.resize(input_size);
        outputs.resize(output_size);
    }

    std::vector<double> forward(const std::vector<double>& input) {
        inputs = input;

        // 隐层 = tanh(W1 * input + b1)
        std::vector<double> hidden(hidden_size);
        for (int j = 0; j < hidden_size; ++j) {
            hidden[j] = biases[j];
            for (int i = 0; i < input_size; ++i) {
                hidden[j] += weights[0][j * input_size + i] * input[i];
            }
            hidden[j] = tanh(hidden[j]);
        }

        // 输出层 = W2 * hidden + b2
        std::vector<double> output(output_size);
        for (int j = 0; j < output_size; ++j) {
            output[j] = biases[hidden_size + j];
            for (int i = 0; i < hidden_size; ++i) {
                output[j] += weights[1][j * hidden_size + i] * hidden[i];
            }
        }

        outputs = output;
        return outputs;
    }

    void updateWeights(const std::vector<double>& grad, double learning_rate) {
        // 简化的梯度下降更新
        for (size_t i = 0; i < weights[1].size() && i < grad.size(); ++i) {
            weights[1][i] -= learning_rate * grad[i];
        }
    }
};

/*
 * ADP控制器类
 */
class ADPController : public BalanceAlgorithm {
public:
    ADPController();

    virtual void reset() override;
    virtual void computeControl(const Eigen::VectorXd& state,
                              const Eigen::VectorXd& target,
                              Eigen::VectorXd& output) override;
    virtual std::string getName() const override { return "ADP"; }

    void setLearningRate(double rate) { learning_rate_ = rate; }
    void setCriticLearningRate(double rate) { critic_learning_rate_ = rate; }

private:
    void updateCritic(const Eigen::VectorXd& state, const Eigen::VectorXd& target);
    void updateAction(const Eigen::VectorXd& state, const Eigen::VectorXd& target);
    std::vector<double> eigenToVector(const Eigen::VectorXd& v);
    Eigen::VectorXd vectorToEigen(const std::vector<double>& v);

    NeuralNetwork action_network_;   // 动作网络
    NeuralNetwork critic_network_;   // 评价网络
    NeuralNetwork target_critic_;    // 目标评价网络

    double learning_rate_;
    double critic_learning_rate_;
    double gamma_;  // 折扣因子

    std::vector<double> prev_critic_value_;
    std::vector<double> prev_action_;

    Eigen::VectorXd prev_state_error_;
    bool is_initialized_;
};

} // namespace balance_control

#endif // ADP_CONTROLLER_H