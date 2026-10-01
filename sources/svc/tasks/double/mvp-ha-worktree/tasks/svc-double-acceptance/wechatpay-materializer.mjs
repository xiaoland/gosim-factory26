import {
  createCipheriv,
  createHash,
  createSign,
} from "node:crypto";
import { readFileSync } from "node:fs";

const input = JSON.parse(await new Promise((resolve) => {
  let raw = "";
  process.stdin.setEncoding("utf8");
  process.stdin.on("data", (chunk) => {
    raw += chunk;
  });
  process.stdin.on("end", () => resolve(raw));
}));
const fixture = JSON.parse(
  readFileSync("tasks/svc-double-acceptance/fixtures/wechatpay.json", "utf8"),
);

const compact = (value) => JSON.stringify(value);
const signRsa = (message) =>
  createSign("sha256WithRSAEncryption")
    .update(message)
    .sign(fixture.platformCertificate.privateKeyPem, "base64");
const signatureHeaders = (bodyText) => {
  const timestamp = String(Math.floor(Date.parse(input.run.clock) / 1000));
  const nonce = createHash("sha256")
    .update(`${input.phase}:${input.scenario.name}:${bodyText}`)
    .digest("hex")
    .slice(0, 32);
  const message = `${timestamp}\n${nonce}\n${bodyText}\n`;
  return {
    "content-type": "application/json; charset=utf-8",
    "wechatpay-timestamp": timestamp,
    "wechatpay-nonce": nonce,
    "wechatpay-serial": fixture.platformCertificate.serialNo,
    "wechatpay-signature": signRsa(message),
  };
};
const encrypt = (plaintext, nonce) => {
  const associatedData = "resource";
  const cipher = createCipheriv("aes-256-gcm", fixture.apiV3Key, nonce).setAAD(
    Buffer.from(associatedData),
  );
  return {
    associatedData,
    ciphertext: Buffer.concat([
      cipher.update(plaintext, "utf8"),
      cipher.final(),
      cipher.getAuthTag(),
    ]).toString("base64"),
  };
};

const rawEnvelope = (status, value) => {
  const bodyText = compact(value);
  return {
    status,
    headers: signatureHeaders(bodyText),
    body: { kind: "raw", base64: Buffer.from(bodyText).toString("base64") },
  };
};

const certificateResponse = () => {
  const nonce = "svc-double01";
  const encrypted = encrypt(fixture.platformCertificate.publicKeyPem, nonce);
  return rawEnvelope(200, {
    data: [
      {
        effective_time: "2026-01-01T00:00:00+00:00",
        encrypt_certificate: {
          algorithm: "AEAD_AES_256_GCM",
          associated_data: encrypted.associatedData,
          ciphertext: encrypted.ciphertext,
          nonce,
        },
        expire_time: "2099-12-31T23:59:59+00:00",
        serial_no: fixture.platformCertificate.serialNo,
      },
    ],
  });
};

const eventEnvelope = () => {
  const outTradeNo = input.bindings.out_trade_no;
  const payerOpenId = input.bindings.payer_openid;
  const total = input.bindings.amount_total;
  if (typeof outTradeNo !== "string" || typeof payerOpenId !== "string" || typeof total !== "number") {
    throw new Error("WeChat Pay event requires captured prepay bindings");
  }
  const resource = compact({
    appid: fixture.appId,
    mchid: fixture.mchId,
    out_trade_no: outTradeNo,
    transaction_id: `svc_tx_${outTradeNo}`,
    trade_state: "SUCCESS",
    trade_state_desc: "支付成功",
    amount: { total, currency: "CNY" },
    payer: { openid: payerOpenId },
  });
  const nonce = "svc-event001";
  const encrypted = encrypt(resource, nonce);
  const bodyText = compact({
    create_time: input.run.clock,
    event_type: "TRANSACTION.SUCCESS",
    id: `svc-notify-${outTradeNo}`,
    resource: {
      algorithm: "AEAD_AES_256_GCM",
      associated_data: encrypted.associatedData,
      ciphertext: encrypted.ciphertext,
      nonce,
      original_type: "transaction",
    },
    resource_type: "encrypt-resource",
    summary: "支付成功",
  });
  return {
    method: "POST",
    path: input.scenario.name.replace("wechatpay-", "/api/payment/wechat-pay/") + "/notify/charge",
    query: {},
    headers: signatureHeaders(bodyText),
    body: { kind: "raw", base64: Buffer.from(bodyText).toString("base64") },
  };
};

let output;
if (input.phase === "event") {
  output = eventEnvelope();
} else if (process.env.ACTION === "certificates") {
  output = certificateResponse();
} else if (process.env.ACTION === "prepay") {
  output = rawEnvelope(200, { prepay_id: "svc_double_prepay_001" });
} else {
  throw new Error(`Unsupported WeChat Pay materializer action: ${process.env.ACTION}`);
}
process.stdout.write(JSON.stringify(output));
