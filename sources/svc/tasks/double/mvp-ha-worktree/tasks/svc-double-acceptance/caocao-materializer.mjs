import { createHash } from "node:crypto";
import { mkdirSync, readFileSync, renameSync, writeFileSync } from "node:fs";
import path from "node:path";

const input = JSON.parse(await new Promise((resolve) => {
  let raw = "";
  process.stdin.setEncoding("utf8");
  process.stdin.on("data", (chunk) => {
    raw += chunk;
  });
  process.stdin.on("end", () => resolve(raw));
}));

const PROVIDER_ORDER_ID = "svc-caocao-order-001";
const SIGN_KEY = "svc-double-caocao-sign-key";
const phases = new Set([
  "CREATED",
  "ACCEPTED",
  "ARRIVED_AT_PICKUP",
  "IN_TRIP",
  "FINISHED",
  "CANCELLED",
]);

const externalOrderId = () => {
  const value = input.bindings.external_order_id;
  if (typeof value !== "string") throw new Error("Caocao order state requires external_order_id");
  return value;
};

const statePath = () => {
  const directory = path.resolve(".dev-server", "svc-double-materializer-state");
  mkdirSync(directory, { recursive: true });
  return path.join(directory, `${createHash("sha256").update(externalOrderId()).digest("hex")}.phase`);
};

const writePhase = (phase) => {
  if (!phases.has(phase)) throw new Error(`Unsupported Caocao phase: ${phase}`);
  const destination = statePath();
  const temporary = `${destination}.${process.pid}.tmp`;
  writeFileSync(temporary, `${phase}\n`, "utf8");
  renameSync(temporary, destination);
};

const readPhase = () => {
  try {
    const phase = readFileSync(statePath(), "utf8").trim();
    return phases.has(phase) ? phase : "CREATED";
  } catch {
    return "CREATED";
  }
};

const success = (data) => ({ code: 200, data, msg: "OK", success: true });
const failure = (code, msg) => ({ code, data: null, msg, success: false });

const estimate = (carType) => {
  const premier = carType === "5";
  const amount = premier ? 5200 : 3600;
  return {
    carType: Number(carType),
    detail: [
      { amount: Math.round(amount * 0.65), chargeCode: "base_fee", chargeDesc: "基础费" },
      {
        amount: amount - Math.round(amount * 0.65),
        chargeCode: "distance_fee",
        chargeDesc: "里程费",
      },
    ],
    distance: 8200,
    duration: 1500,
    lineType: 0,
    name: premier ? "专车" : "快车",
    originPrice: amount,
    price: amount,
    priceKey: `svc_quote_${carType}_${amount}`,
  };
};

const orderDetail = () => {
  const phase = readPhase();
  const status = {
    CREATED: "1",
    ACCEPTED: "9",
    ARRIVED_AT_PICKUP: "12",
    IN_TRIP: "3",
    FINISHED: "5",
    CANCELLED: "20",
  }[phase];
  return {
    basicOrderVO: {
      orderId: PROVIDER_ORDER_ID,
      requireLevel: 3,
      status,
    },
    driverInfoVo:
      phase === "CREATED"
        ? null
        : {
            avatar: "https://example.invalid/svc-double-driver.png",
            carBrand: "几何",
            card: "浙A12345",
            color: "白色",
            location: { lat: 30.2912, lng: 120.212 },
            name: "曹操测试司机",
            phone: "13900139000",
            phone_passenger: "13900139000",
          },
    orderFeeVo: {
      totalFee: phase === "FINISHED" ? 4000 : null,
    },
  };
};

const responseValue = () => {
  switch (process.env.ACTION) {
    case "city":
      return success({ city_code: "0571", city_name: "杭州市" });
    case "estimate-3":
      return success(estimate("3"));
    case "estimate-5":
      return success(estimate("5"));
    case "unavailable":
      return failure(47001, "Caocao vehicle unavailable for this boundary claim");
    case "create-success": {
      writePhase("CREATED");
      return success({ orderNo: PROVIDER_ORDER_ID });
    }
    case "create-failure":
      return failure(50001, "Fake Caocao create failed");
    case "order-detail":
      return success(orderDetail());
    case "driver-location":
      return success({ direction: 90, lat: 30.2912, lng: 120.212, speed: 28 });
    case "polyline-pickup":
      return success({
        driverEtaInfoVO: {
          lat: 30.2912,
          lng: 120.212,
          remainDistance: 1200,
          remainLightCount: 2,
          remainTime: 240,
        },
        navigationPolylineType: 1,
        steps: [{ links: [{ coords: "30.2912,120.212;30.2900,120.2000" }] }],
      });
    case "polyline-dropoff":
      return success({
        driverEtaInfoVO: {
          lat: 30.24,
          lng: 120.102,
          remainDistance: 1600,
          remainLightCount: 3,
          remainTime: 300,
        },
        navigationPolylineType: 3,
        steps: [{ links: [{ coords: "30.2912,120.212;30.24,120.102" }] }],
      });
    case "cancel-fee":
      return success({
        cancelFee: Number(process.env.CANCEL_FEE ?? "800"),
        orderNo: PROVIDER_ORDER_ID,
      });
    case "cancel":
      writePhase("CANCELLED");
      return success({
        cancelFee: Number(process.env.CANCEL_FEE ?? "800"),
        orderNo: PROVIDER_ORDER_ID,
      });
    case "fee-confirm":
      return success(null);
    default:
      throw new Error(`Unsupported Caocao materializer action: ${process.env.ACTION}`);
  }
};

const sign = (params) => {
  const source = Object.entries({ ...params, sign_key: SIGN_KEY })
    .sort(([left], [right]) => (left < right ? -1 : left > right ? 1 : 0))
    .map(([key, value]) => `${key}${value}`)
    .join("");
  return createHash("sha1").update(source, "utf8").digest("hex");
};

const eventEnvelope = () => {
  const externalOrderId = input.bindings.external_order_id;
  const callbackInfo = input.bindings.callback_info;
  if (typeof externalOrderId !== "string" || typeof callbackInfo !== "string") {
    throw new Error("Caocao event requires captured order and callback bindings");
  }
  const eventCodes = {
    "order.accepted": "1",
    "order.arrived": "3",
    "order.in-trip": "4",
    "order.finished": "6",
  };
  const eventPhases = {
    "order.accepted": "ACCEPTED",
    "order.arrived": "ARRIVED_AT_PICKUP",
    "order.in-trip": "IN_TRIP",
    "order.finished": "FINISHED",
  };
  const event = eventCodes[process.env.EVENT];
  if (!event) throw new Error(`Unsupported Caocao event: ${process.env.EVENT}`);
  writePhase(eventPhases[process.env.EVENT]);
  const params = {
    callback_info: callbackInfo,
    event,
    ext_order_id: externalOrderId,
    order_id: PROVIDER_ORDER_ID,
    timestamp: String(Date.parse(input.run.clock)),
    car_no: "浙A12345",
    driver_name: "曹操测试司机",
    driver_phone: "13900139000",
    vehicle_brand: "几何",
    vehicle_color: "白色",
    ...(event === "6" ? { final_amount_fen: "4000" } : {}),
  };
  const body = new URLSearchParams({ ...params, sign: sign(params) }).toString();
  return {
    method: "POST",
    path: "/api/v1/service_provider/caocao/callback/order",
    query: {},
    headers: { "content-type": "application/x-www-form-urlencoded" },
    body: { kind: "raw", base64: Buffer.from(body).toString("base64") },
  };
};

const output =
  input.phase === "event"
    ? eventEnvelope()
    : {
        status: 200,
        headers: { "content-type": "application/json; charset=utf-8" },
        body: { kind: "structured", value: responseValue() },
      };

process.stdout.write(JSON.stringify(output));
