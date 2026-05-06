/*
 * ADP Controller Implementation
 * =============================
 */

#include "adp_controller.h"
#include <cmath>
#include <algorithm>

namespace balance_control {

ADPController::ADPController()
    : learning_rate_(0.01)
    , critic_learning_rate_(0.005)
    , gamma_(0.99)
    , is_initialized_(false)
{
    srand(time(nullptr));

    int state_dim = 6;
    int action_dim = 6;
    int hidden_dim = 12;

    action_network_ = NeuralNetwork(state_dim, hidden_dim, action_dim);
    critic_network_ = NeuralNetwork(state_dim + action_dim, hidden_dim, 1);
    target_critic_ = NeuralNetwork(state_dim + action_dim, hidden_dim, 1);

    prev_critic_value_.resize(1, 0.0);
    prev_action_.resize(action_dim, 0.0);
    prev_state_error_.resize(state_dim);
}

void ADPController::reset() {
    prev_critic_value_[0] = 0.0;
    std::fill(prev_action_.begin(), prev_action_.end(), 0.0);
    prev_state_error_.setZero();
    is_initialized_ = false;
}

std::vector<double> ADPController::eigenToVector(const Eigen::VectorXd& v) {
    std::vector<double> result(v.size());
    for (int i = 0; i < v.size(); ++i) {
        result[i] = v(i);
    }
    return result;
}

Eigen::VectorXd ADPController::vectorToEigen(const std::vector<double>& v) {
    Eigen::VectorXd result(v.size());
    for (size_t i = 0; i < v.size(); ++i) {
        result(i) = v[i];
    }
    return result;
}

void ADPController::updateCritic(const Eigen::VectorXd& state, const Eigen::VectorXd& target) {
    Eigen::VectorXd error = target - state;

    std::vector<double> state_vec = eigenToVector(error);
    std::vector<double> action_vec = prev_action_;

    std::vector<double> critic_input(state_vec);
    critic_input.insert(critic_input.end(), action_vec.begin(), action_vec.end());

    std::vector<double> critic_output = critic_network_.forward(critic_input);

    double td_error = 0.0;
    if (is_initialized_) {
        td_error = -critic_output[0] + prev_critic_value_[0];
    }

    std::vector<double> grad(1, td_error);
    critic_network_.updateWeights(grad, critic_learning_rate_);

    prev_critic_value_ = critic_output;
}

void ADPController::updateAction(const Eigen::VectorXd& state, const Eigen::VectorXd& target) {
    Eigen::VectorXd error = target - state;

    std::vector<double> state_vec = eigenToVector(error);
    std::vector<double> action_vec = action_network_.forward(state_vec);

    std::vector<double> critic_input(state_vec);
    critic_input.insert(critic_input.end(), action_vec.begin(), action_vec.end());

    std::vector<double> critic_output = critic_network_.forward(critic_input);

    std::vector<double> action_grad(action_vec.size(), 0.0);
    for (size_t i = 0; i < action_grad.size(); ++i) {
        action_grad[i] = -critic_output[0] * 0.1;
    }

    action_network_.updateWeights(action_grad, learning_rate_);

    prev_action_ = action_vec;
}

void ADPController::computeControl(const Eigen::VectorXd& state,
                                   const Eigen::VectorXd& target,
                                   Eigen::VectorXd& output) {
    if (output.size() != 12) {
        output.resize(12);
    }

    if (state.size() != 6 || target.size() != 6) {
        output.setZero();
        return;
    }

    Eigen::VectorXd error = target - state;

    std::vector<double> state_vec = eigenToVector(error);
    std::vector<double> action_vec = action_network_.forward(state_vec);

    Eigen::VectorXd u = vectorToEigen(action_vec);

    if (is_initialized_) {
        updateCritic(state, target);
        updateAction(state, target);
    }
    is_initialized_ = true;

    prev_state_error_ = error;

    output.setZero();
    output(0) = u(0);  // 左髋横滚
    output(1) = u(1);  // 左髋俯仰
    output(2) = u(1) * 0.5;  // 左膝俯仰
    output(3) = 0.0;  // 左轮
    output(4) = -u(0);  // 右髋横滚
    output(5) = u(1);  // 右髋俯仰
    output(6) = u(1) * 0.5;  // 右膝俯仰
    output(7) = 0.0;  // 右轮

    double max_torque = params_.max_torque;
    for (int i = 0; i < 8; ++i) {
        if (output(i) > max_torque) output(i) = max_torque;
        if (output(i) < -max_torque) output(i) = -max_torque;
    }
}

} // namespace balance_control