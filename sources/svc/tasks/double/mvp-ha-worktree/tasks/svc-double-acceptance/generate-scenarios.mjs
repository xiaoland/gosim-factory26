import { mkdirSync, writeFileSync } from "node:fs";
import path from "node:path";

const output = process.argv[2];
if (!output) throw new Error("Usage: generate-scenarios.mjs OUTPUT_DIRECTORY");
mkdirSync(output, { recursive: true });

const CLIENT_ID = "svc-double-caocao-client";
const SIGN_KEY = "svc-double-caocao-sign-key";

const exact = (value) => ({ type: "exact", value });
const regex = (pattern) => ({ type: "match", pattern });
const capture = (name, pattern) => ({ type: "capture", name, pattern });

const renderFields = (fields, spaces) =>
  Object.entries(fields)
    .map(([name, spec]) => {
      const indent = " ".repeat(spaces);
      if (spec.type === "exact") return `${indent}${name}: ${JSON.stringify(spec.value)}`;
      const captureLine = spec.type === "capture" ? `\n${indent}    name: ${spec.name}` : "";
      return (
        `${indent}${name}:\n` +
        `${indent}  $bsl:\n` +
        `${indent}    kind: ${spec.type}${captureLine}\n` +
        `${indent}    match: {kind: regex, pattern: ${JSON.stringify(spec.pattern)}}`
      );
    })
    .join("\n");

const signed = (fields) => ({
  ...fields,
  client_id: exact(CLIENT_ID),
  timestamp: regex("^[0-9]{13}$"),
  sign: regex("^[0-9a-f]{40}$"),
});

const materializer = (action, extraEnv = {}) => {
  const env = Object.entries({ ACTION: action, ...extraEnv })
    .map(([key, value]) => `${key}: ${JSON.stringify(String(value))}`)
    .join(", ");
  return (
    "      response:\n" +
    "        status: 200\n" +
    "        materializer:\n" +
    "          argv: [node, tasks/svc-double-acceptance/caocao-materializer.mjs]\n" +
    "          cwd: ../..\n" +
    `          env: {${env}}\n` +
    "          timeout-ms: 2000\n" +
    "          max-output-bytes: 1048576\n"
  );
};

const queryInteraction = (name, requestPath, fields, action, extraEnv = {}) =>
  "    - name: " + name + "\n" +
  "      provenance: {kind: consumer-requirement, source: https://partner-up.test/system-scenario/ride-hailing}\n" +
  "      request:\n" +
  "        method: GET\n" +
  `        path: ${requestPath}\n` +
  "        query:\n" +
  renderFields(signed(fields), 10) + "\n" +
  materializer(action, extraEnv);

const formInteraction = (name, requestPath, fields, action, extraEnv = {}) =>
  "    - name: " + name + "\n" +
  "      provenance: {kind: consumer-requirement, source: https://partner-up.test/system-scenario/ride-hailing}\n" +
  "      request:\n" +
  "        method: POST\n" +
  `        path: ${requestPath}\n` +
  "        headers: {content-type: application/x-www-form-urlencoded}\n" +
  "        body:\n" +
  "          form-urlencoded:\n" +
  renderFields(signed(fields), 12) + "\n" +
  materializer(action, extraEnv);

const createFields = (mode) => ({
  callback_info: capture("callback_info", "^pu\\.rhc\\.v1\\.stg\\.[0-9a-f-]{36}$"),
  caller_phone: regex("^1[0-9]{10}$"),
  city_code: exact("0571"),
  end_address: exact("杭州市西湖区灵隐路1号"),
  end_name: exact("灵隐寺"),
  ext_order_id: capture("external_order_id", "^rh[0-9a-z]+$"),
  from_latitude: exact("30.2912"),
  from_longitude: exact("120.212"),
  is_simultaneously_call: exact(mode === "multi" ? "1" : "0"),
  order_type: exact("1"),
  passenger_name: regex("^.+$"),
  passenger_phone: regex("^1[0-9]{10}$"),
  start_address: exact("杭州市上城区全福桥路2号"),
  start_name: exact("杭州东站"),
  to_latitude: exact("30.24"),
  to_longitude: exact("120.102"),
  ...(mode === "multi"
    ? {
        service_type_price: exact(
          '[{"estimateKey":"svc_quote_3_3600","estimatePrice":3600,"serviceType":3},{"estimateKey":"svc_quote_5_5200","estimatePrice":5200,"serviceType":5}]',
        ),
      }
    : {
        car_type: exact("3"),
        estimate_price: exact("3600"),
        estimate_price_key: exact("svc_quote_3_3600"),
      }),
});

const events = () =>
  [
    ["order.accepted", "order.accepted"],
    ["order.arrived", "order.arrived"],
    ["order.in-trip", "order.in-trip"],
    ["order.finished", "order.finished"],
  ]
    .map(
      ([name, event]) =>
        "    - name: " + name + "\n" +
        "      target: consumer.backend\n" +
        "      provenance: {kind: consumer-requirement, source: https://partner-up.test/system-scenario/ride-hailing}\n" +
        "      request:\n" +
        "        method: POST\n" +
        "        path: /api/v1/service_provider/caocao/callback/order\n" +
        "        materializer:\n" +
        "          argv: [node, tasks/svc-double-acceptance/caocao-materializer.mjs]\n" +
        "          cwd: ../..\n" +
        `          env: {EVENT: ${JSON.stringify(event)}}\n` +
        "          timeout-ms: 2000\n" +
        "          max-output-bytes: 1048576\n",
    )
    .join("");

const caocaoModule = (name, config) => {
  const interactions = [
    queryInteraction(
      "query-city",
      "/common/queryCity",
      { latitude: exact("30.2912"), longitude: exact("120.212") },
      "city",
    ),
    queryInteraction(
      "estimate-fast",
      "/common/estimatePriceWithDetail",
      {
        car_type: exact("3"), city_code: exact("0571"), from_latitude: exact("30.2912"),
        from_longitude: exact("120.212"), order_type: exact("1"), to_latitude: exact("30.24"),
        to_longitude: exact("120.102"), carpool_type: exact("0"), count_person: exact("2"),
      },
      config.unavailable.has("3") ? "unavailable" : "estimate-3",
    ),
    queryInteraction(
      "estimate-premier",
      "/common/estimatePriceWithDetail",
      {
        car_type: exact("5"), city_code: exact("0571"), from_latitude: exact("30.2912"),
        from_longitude: exact("120.212"), order_type: exact("1"), to_latitude: exact("30.24"),
        to_longitude: exact("120.102"), carpool_type: exact("0"), count_person: exact("2"),
      },
      config.unavailable.has("5") ? "unavailable" : "estimate-5",
    ),
  ];
  if (config.createMode) {
    interactions.push(
      formInteraction(
        "create-ride",
        "/common/orderCarV2",
        createFields(config.createMode),
        config.createFailure ? "create-failure" : "create-success",
      ),
    );
  }
  if (config.createMode && !config.createFailure) {
    interactions.push(
      queryInteraction(
        "query-order-detail",
        "/common/queryOrderDetailV2",
        { order_id: exact("svc-caocao-order-001") },
        "order-detail",
      ),
      queryInteraction(
        "query-driver-location",
        "/common/queryDriverLocationByOrderId",
        { order_id: exact("svc-caocao-order-001") },
        "driver-location",
      ),
      formInteraction(
        "query-pickup-polyline",
        "/common/queryDriverPolyline",
        { navigation_polyline_type: exact("1"), order_id: exact("svc-caocao-order-001") },
        "polyline-pickup",
      ),
      formInteraction(
        "query-dropoff-polyline",
        "/common/queryDriverPolyline",
        { navigation_polyline_type: exact("3"), order_id: exact("svc-caocao-order-001") },
        "polyline-dropoff",
      ),
      queryInteraction(
        "query-cancel-fee",
        "/common/queryCancelFee",
        { order_no: exact("svc-caocao-order-001") },
        "cancel-fee",
        { CANCEL_FEE: config.cancelFee },
      ),
      formInteraction(
        "cancel-ride",
        "/common/cancelOrderV3",
        {
          order_id: exact("svc-caocao-order-001"),
          cancel_code: regex("^.+$"),
          cancel_reason: regex("^.+$"),
          who_cancel: regex("^.+$"),
        },
        "cancel",
        { CANCEL_FEE: config.cancelFee },
      ),
      formInteraction(
        "confirm-fee",
        "/common/feeConfirm",
        { order_id: exact("svc-caocao-order-001") },
        "fee-confirm",
      ),
    );
  }
  return (
    "language: svc.double/v0\n\n" +
    "scenario:\n" +
    `  name: caocao-${name}\n` +
    `  claim: ${JSON.stringify(`the real Consumer satisfies the ${name} ride-hailing product scenario`)}\n` +
    "  boundary: {name: caocao-provider, protocol: http}\n" +
    "  policy: {event-targets: loopback-only}\n" +
    "  interactions:\n" +
    interactions.join("") +
    (config.createMode && !config.createFailure ? "  events:\n" + events() : "")
  );
};

const variants = {
  "default-multi": { createMode: "multi", createFailure: false, unavailable: new Set(), cancelFee: 800 },
  "default-single": { createMode: "single", createFailure: false, unavailable: new Set(), cancelFee: 800 },
  "cancel-zero": { createMode: "single", createFailure: false, unavailable: new Set(), cancelFee: 0 },
  "create-failure": { createMode: "multi", createFailure: true, unavailable: new Set(), cancelFee: 800 },
  "unavailable-5": { createMode: "single", createFailure: false, unavailable: new Set(["5"]), cancelFee: 800 },
  "unavailable-all": { createMode: null, createFailure: false, unavailable: new Set(["3", "5"]), cancelFee: 800 },
};
for (const [name, config] of Object.entries(variants)) {
  writeFileSync(path.join(output, `caocao-${name}.double.yaml`), caocaoModule(name, config));
}

const wechatpay = `language: svc.double/v0

scenario:
  name: wechatpay-00000000-0000-4000-8000-000000000000
  claim: the real Consumer exposes a paid bill after a signed WeChat Pay success notification
  boundary: {name: wechatpay-provider, protocol: http}
  policy: {event-targets: loopback-only}
  interactions:
    - name: certificates
      provenance: {kind: consumer-requirement, source: https://partner-up.test/system-scenario/payment}
      request: {method: GET, path: /v3/certificates}
      response:
        status: 200
        materializer:
          argv: [node, tasks/svc-double-acceptance/wechatpay-materializer.mjs]
          cwd: ../..
          env: {ACTION: certificates}
          timeout-ms: 2000
          max-output-bytes: 1048576
    - name: create-jsapi-prepay
      provenance: {kind: consumer-requirement, source: https://partner-up.test/system-scenario/payment}
      request:
        method: POST
        path: /v3/pay/transactions/jsapi
        body:
          structured:
            appid: wx_fake_partnerup_web
            mchid: "1900000001"
            description:
              $bsl: {kind: match, match: {kind: regex, pattern: "^.+$"}}
            out_trade_no:
              $bsl: {kind: capture, name: out_trade_no, match: {kind: regex, pattern: "^PC[A-Za-z0-9_-]{30}$"}}
            notify_url:
              $bsl: {kind: capture, name: notify_url, match: {kind: regex, pattern: "^http://127[.]0[.]0[.]1:[0-9]+/api/payment/wechat-pay/[0-9a-f-]{36}/notify/charge$"}}
            amount:
              total:
                $bsl: {kind: capture, name: amount_total, match: {kind: range, minimum: 1, maximum: 1000000}}
              currency: CNY
            payer:
              openid:
                $bsl: {kind: capture, name: payer_openid, match: {kind: regex, pattern: "^.+$"}}
            time_expire:
              $bsl: {kind: match, match: {kind: semantic, semantic: rfc3339, using: svc.rfc3339/v1}}
      response:
        status: 200
        materializer:
          argv: [node, tasks/svc-double-acceptance/wechatpay-materializer.mjs]
          cwd: ../..
          env: {ACTION: prepay}
          timeout-ms: 2000
          max-output-bytes: 1048576
  events:
    - name: payment.succeeded
      target: consumer.backend
      provenance: {kind: consumer-requirement, source: https://partner-up.test/system-scenario/payment}
      request:
        method: POST
        path: /api/payment/wechat-pay/00000000-0000-4000-8000-000000000000/notify/charge
        materializer:
          argv: [node, tasks/svc-double-acceptance/wechatpay-materializer.mjs]
          cwd: ../..
          env: {EVENT: payment.succeeded}
          timeout-ms: 2000
          max-output-bytes: 1048576
`;
writeFileSync(path.join(output, "wechatpay-bootstrap.double.yaml"), wechatpay);
