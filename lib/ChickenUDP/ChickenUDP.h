#include <ArduinoJson.h>
#include <CRC32.h>
#include "const.h"

class ChickenUDP {
 protected:
  CRC32 crc;

 public:
  String packageData(DataJson *app_data) {
    String app_data_str;
    char checksum_hex[9];
    serializeJson(*app_data, app_data_str);

    crc.add((uint8_t *)app_data_str.c_str(), strlen(app_data_str.c_str()));
    sprintf(checksum_hex, "%08x", crc.calc());
    String cudp_packet = app_data_str + checksum_hex;

    crc.restart();
    return cudp_packet;
  };

  bool unpackData(const String &cudp_packet, JsonObject *app_data) {
    int string_length = cudp_packet.length();
    String app_data_str = cudp_packet.substring(0, string_length - 8);
    String checksum_str = cudp_packet.substring(string_length - 8);
    crc.add((uint8_t *)app_data_str.c_str(), strlen(app_data_str.c_str()));

    uint32_t checksum_in_packet = strtoimax(checksum_str.c_str(), nullptr, 16);
    uint32_t checksum_recalculated = crc.calc();
    crc.restart();

    if (checksum_in_packet != checksum_recalculated) return false;

    DataJson app_data_doc;
    deserializeJson(app_data_doc, app_data_str);

    *app_data = app_data_doc.as<JsonObject>();
    return true;
  };
};