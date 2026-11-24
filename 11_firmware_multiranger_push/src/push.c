#include <string.h>
#include <stdint.h>
#include <stdbool.h>

#include "app.h"
#include "commander.h"
#include "FreeRTOS.h"
#include "task.h"
#include "debug.h"
#include "log.h"
#include "param.h"

#define DEBUG_MODULE "PUSH"

static void setHoverSetpoint(setpoint_t *setpoint, float vx, float vy, float z, float yawrate)
{
  setpoint->mode.z = modeAbs;
  setpoint->position.z = z;

  setpoint->mode.yaw = modeVelocity;
  setpoint->attitudeRate.yaw = yawrate;

  setpoint->mode.x = modeVelocity;
  setpoint->mode.y = modeVelocity;
  setpoint->velocity.x = vx;
  setpoint->velocity.y = vy;

  setpoint->velocity_body = true;
}

typedef enum {
  idle,
  lowUnlock,
  unlocked,
  landing,
  stopping
} State;

static State state = idle;

static const uint16_t unlockThLow = 100;
static const uint16_t unlockThHigh = 300;
static const uint16_t stoppedTh = 500;

static const float velMax = 1.0f;
static const uint16_t radius = 300;
static const float height_sp = 0.5f;        // Hover height in meters
static const float landingStartH = 0.20f;   // Automatic landing triggers below this height
static const float landingEndH = 0.02f;     // Final target height before shutting off motors (2 cm)
static const float landingStep = 0.0015f;   // 0.0015 m every 10 ms = 0.15 m/s

static float current_height = 0.65f;
static uint16_t landingTimeout = 0;

#define MAX(a,b) ((a>b)?a:b)
#define MIN(a,b) ((a<b)?a:b)

void appMain()
{
  static setpoint_t setpoint;

  vTaskDelay(M2T(3000));

  logVarId_t idUp = logGetVarId("range", "up");
  logVarId_t idLeft = logGetVarId("range", "left");
  logVarId_t idRight = logGetVarId("range", "right");
  logVarId_t idFront = logGetVarId("range", "front");
  logVarId_t idBack = logGetVarId("range", "back");
  logVarId_t idZ = logGetVarId("stateEstimate", "z");

  paramVarId_t idPositioningDeck = paramGetVarId("deck", "bcFlow2");
  paramVarId_t idMultiranger = paramGetVarId("deck", "bcMultiranger");

  float factor = velMax / radius;

  DEBUG_PRINT("Waiting for activation ...\n");

  while (1) {
    vTaskDelay(M2T(10));

    uint8_t positioningInit = paramGetUint(idPositioningDeck);
    uint8_t multirangerInit = paramGetUint(idMultiranger);

    uint16_t up = logGetUint(idUp);

    if (state == unlocked) {
      uint16_t left = logGetUint(idLeft);
      uint16_t right = logGetUint(idRight);
      uint16_t front = logGetUint(idFront);
      uint16_t back = logGetUint(idBack);

      uint16_t left_o = radius - MIN(left, radius);
      uint16_t right_o = radius - MIN(right, radius);
      float l_comp = (-1) * left_o * factor;
      float r_comp = right_o * factor;
      float velSide = r_comp + l_comp;

      uint16_t front_o = radius - MIN(front, radius);
      uint16_t back_o = radius - MIN(back, radius);
      float f_comp = (-1) * front_o * factor;
      float b_comp = back_o * factor;
      float velFront = b_comp + f_comp;

      if (up > 0 && up < radius) {
        current_height -= 0.004f; // Descends at ~0.4 m/s while hand is above
      }

      if (current_height <= landingStartH) {
        state = landing;
        landingTimeout = 0;
        DEBUG_PRINT("Smooth landing...\n");
      }

      setHoverSetpoint(&setpoint, velFront, velSide, current_height, 0);
      commanderSetSetpoint(&setpoint, 3);
    } else if (state == landing) {
      float z_est = logGetFloat(idZ);

      if (current_height > landingEndH) {
        current_height -= landingStep;
        if (current_height < landingEndH) {
          current_height = landingEndH;
        }
      } else {
        landingTimeout++;
      }

      // Shut off motors only when setpoint is at 2 cm and drone is actually close to the ground
      // (or after ~1 s safety timeout at minimum height)
      if (current_height <= landingEndH && (z_est < 0.05f || landingTimeout > 100)) {
        state = stopping;
        DEBUG_PRINT("Motors off\n");
      } else {
        setHoverSetpoint(&setpoint, 0.0f, 0.0f, current_height, 0);
        commanderSetSetpoint(&setpoint, 3);
      }
    } else {
      if (state == stopping && up > stoppedTh) {
        state = idle;
        DEBUG_PRINT("Idle\n");
      }

      if (up < unlockThLow && state == idle && up > 0.001f) {
        DEBUG_PRINT("Waiting for hand to be removed!\n");
        state = lowUnlock;
      }

      if (up > unlockThHigh && state == lowUnlock && positioningInit && multirangerInit) {
        DEBUG_PRINT("Unlocked!\n");
        current_height = height_sp;
        landingTimeout = 0;
        state = unlocked;
      }

      if (state == idle || state == stopping) {
        memset(&setpoint, 0, sizeof(setpoint_t));
        commanderSetSetpoint(&setpoint, 3);
      }
    }
  }
}