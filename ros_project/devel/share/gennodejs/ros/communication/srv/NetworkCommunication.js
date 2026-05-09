// Auto-generated. Do not edit!

// (in-package communication.srv)


"use strict";

const _serializer = _ros_msg_utils.Serialize;
const _arraySerializer = _serializer.Array;
const _deserializer = _ros_msg_utils.Deserialize;
const _arrayDeserializer = _deserializer.Array;
const _finder = _ros_msg_utils.Find;
const _getByteLength = _ros_msg_utils.getByteLength;

//-----------------------------------------------------------


//-----------------------------------------------------------

class NetworkCommunicationRequest {
  constructor(initObj={}) {
    if (initObj === null) {
      // initObj === null is a special case for deserialization where we don't initialize fields
      this.server_ip = null;
      this.server_port = null;
      this.message = null;
    }
    else {
      if (initObj.hasOwnProperty('server_ip')) {
        this.server_ip = initObj.server_ip
      }
      else {
        this.server_ip = '';
      }
      if (initObj.hasOwnProperty('server_port')) {
        this.server_port = initObj.server_port
      }
      else {
        this.server_port = 0;
      }
      if (initObj.hasOwnProperty('message')) {
        this.message = initObj.message
      }
      else {
        this.message = '';
      }
    }
  }

  static serialize(obj, buffer, bufferOffset) {
    // Serializes a message object of type NetworkCommunicationRequest
    // Serialize message field [server_ip]
    bufferOffset = _serializer.string(obj.server_ip, buffer, bufferOffset);
    // Serialize message field [server_port]
    bufferOffset = _serializer.int32(obj.server_port, buffer, bufferOffset);
    // Serialize message field [message]
    bufferOffset = _serializer.string(obj.message, buffer, bufferOffset);
    return bufferOffset;
  }

  static deserialize(buffer, bufferOffset=[0]) {
    //deserializes a message object of type NetworkCommunicationRequest
    let len;
    let data = new NetworkCommunicationRequest(null);
    // Deserialize message field [server_ip]
    data.server_ip = _deserializer.string(buffer, bufferOffset);
    // Deserialize message field [server_port]
    data.server_port = _deserializer.int32(buffer, bufferOffset);
    // Deserialize message field [message]
    data.message = _deserializer.string(buffer, bufferOffset);
    return data;
  }

  static getMessageSize(object) {
    let length = 0;
    length += _getByteLength(object.server_ip);
    length += _getByteLength(object.message);
    return length + 12;
  }

  static datatype() {
    // Returns string type for a service object
    return 'communication/NetworkCommunicationRequest';
  }

  static md5sum() {
    //Returns md5sum for a message object
    return '2f46b466a2dbd73e7ed3420e141c6cca';
  }

  static messageDefinition() {
    // Returns full string definition for message
    return `
    string server_ip
    int32 server_port
    string message
    
    `;
  }

  static Resolve(msg) {
    // deep-construct a valid message object instance of whatever was passed in
    if (typeof msg !== 'object' || msg === null) {
      msg = {};
    }
    const resolved = new NetworkCommunicationRequest(null);
    if (msg.server_ip !== undefined) {
      resolved.server_ip = msg.server_ip;
    }
    else {
      resolved.server_ip = ''
    }

    if (msg.server_port !== undefined) {
      resolved.server_port = msg.server_port;
    }
    else {
      resolved.server_port = 0
    }

    if (msg.message !== undefined) {
      resolved.message = msg.message;
    }
    else {
      resolved.message = ''
    }

    return resolved;
    }
};

class NetworkCommunicationResponse {
  constructor(initObj={}) {
    if (initObj === null) {
      // initObj === null is a special case for deserialization where we don't initialize fields
      this.success = null;
      this.response = null;
    }
    else {
      if (initObj.hasOwnProperty('success')) {
        this.success = initObj.success
      }
      else {
        this.success = false;
      }
      if (initObj.hasOwnProperty('response')) {
        this.response = initObj.response
      }
      else {
        this.response = '';
      }
    }
  }

  static serialize(obj, buffer, bufferOffset) {
    // Serializes a message object of type NetworkCommunicationResponse
    // Serialize message field [success]
    bufferOffset = _serializer.bool(obj.success, buffer, bufferOffset);
    // Serialize message field [response]
    bufferOffset = _serializer.string(obj.response, buffer, bufferOffset);
    return bufferOffset;
  }

  static deserialize(buffer, bufferOffset=[0]) {
    //deserializes a message object of type NetworkCommunicationResponse
    let len;
    let data = new NetworkCommunicationResponse(null);
    // Deserialize message field [success]
    data.success = _deserializer.bool(buffer, bufferOffset);
    // Deserialize message field [response]
    data.response = _deserializer.string(buffer, bufferOffset);
    return data;
  }

  static getMessageSize(object) {
    let length = 0;
    length += _getByteLength(object.response);
    return length + 5;
  }

  static datatype() {
    // Returns string type for a service object
    return 'communication/NetworkCommunicationResponse';
  }

  static md5sum() {
    //Returns md5sum for a message object
    return '187f74b76a3c78db0f92719010b77755';
  }

  static messageDefinition() {
    // Returns full string definition for message
    return `
    bool success
    string response
    
    `;
  }

  static Resolve(msg) {
    // deep-construct a valid message object instance of whatever was passed in
    if (typeof msg !== 'object' || msg === null) {
      msg = {};
    }
    const resolved = new NetworkCommunicationResponse(null);
    if (msg.success !== undefined) {
      resolved.success = msg.success;
    }
    else {
      resolved.success = false
    }

    if (msg.response !== undefined) {
      resolved.response = msg.response;
    }
    else {
      resolved.response = ''
    }

    return resolved;
    }
};

module.exports = {
  Request: NetworkCommunicationRequest,
  Response: NetworkCommunicationResponse,
  md5sum() { return '1669b1e1911ecbb5ee2158c03f61fe58'; },
  datatype() { return 'communication/NetworkCommunication'; }
};
