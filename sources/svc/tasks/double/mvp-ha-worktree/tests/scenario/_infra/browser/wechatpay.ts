import type { Page } from "playwright";
import { emitWeChatPaySucceeded } from "../double/scenario-doubles";

export async function installWeChatPayDoubleBridge(page: Page): Promise<void> {
  await page.exposeFunction("svcDoubleCompleteWeChatPay", async () => {
    emitWeChatPaySucceeded();
  });
  await page.addInitScript(() => {
    type BridgePayload = {
      package: string;
    };
    type BridgeCallback = (response: { err_msg?: string }) => void;
    type BridgeWindow = Window & {
      svcDoubleCompleteWeChatPay(): Promise<void>;
      WeixinJSBridge: {
        invoke(method: string, payload: BridgePayload, callback: BridgeCallback): void;
      };
    };

    (window as BridgeWindow).WeixinJSBridge = {
      invoke(method, _payload, callback) {
        if (method !== "getBrandWCPayRequest") {
          callback({ err_msg: `${method}:fail` });
          return;
        }
        void (window as BridgeWindow)
          .svcDoubleCompleteWeChatPay()
          .then(() => callback({ err_msg: "get_brand_wcpay_request:ok" }))
          .catch((error: unknown) => {
            callback({
              err_msg:
                error instanceof Error
                  ? `get_brand_wcpay_request:fail ${error.message}`
                  : "get_brand_wcpay_request:fail",
            });
          });
      },
    };
  });
}
