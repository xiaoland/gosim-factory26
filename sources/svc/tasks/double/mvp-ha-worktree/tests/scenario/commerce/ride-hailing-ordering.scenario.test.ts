import assert from "node:assert/strict";
import { randomUUID } from "node:crypto";
import type { Page } from "playwright";
import {
  createOffer,
  createPlacement,
  createProductSpu,
} from "../../../apps/backend/src/domains/merchandising/commands";
import type { PricingModel, SkuFacts } from "../../../apps/backend/src/domains/merchandising/model";
import { registerPaymentProviderInstance } from "../../../apps/backend/src/domains/payment/commands";
import { registerRideHailingProviderInstance } from "../../../apps/backend/src/domains/ride-hailing/commands";
import { commerceQuotes } from "../../../apps/backend/src/entities/commerce-quote";
import type { PRRoute } from "../../../apps/backend/src/entities/partner-request";
import { db } from "../../../apps/backend/src/lib/db";
import { PartnerRepository } from "../../../apps/backend/src/repositories/PartnerRepository";
import { PartnerRequestRepository } from "../../../apps/backend/src/repositories/PartnerRequestRepository";
import { ProductSkuRepository } from "../../../apps/backend/src/repositories/ProductSkuRepository";
import {
  bindScenarioWeChatOpenId,
  configurePRStatus,
} from "../../../apps/backend/tests/pr/_kit/actions/system-state";
import { givenUser, type ScenarioUser } from "../../../apps/backend/tests/pr/_kit/builders/users";
import { withScenarioPage } from "../_infra/browser/browser";
import { installScenarioUserSession } from "../_infra/browser/session";
import { installDeterministicShareSidecarStubs } from "../_infra/browser/share-sidecars";
import { installWeChatPayDoubleBridge } from "../_infra/browser/wechatpay";
import {
  emitCaocaoEvent,
  matchedInteractionCount,
  useCaocaoDouble,
  useWeChatPayDouble,
} from "../_infra/double/scenario-doubles";
import { getScenarioEnvironment } from "../_infra/environment/scenario-environment";
import { scenario } from "../_infra/scenario/scenario";

const partnerRepo = new PartnerRepository();
const partnerRequestRepo = new PartnerRequestRepository();
const productSkuRepo = new ProductSkuRepository();

type ScenarioRideHailingPr = {
  id: number;
};

type FutureRideHailingSkuFacts = {
  rideHailingProviderInstanceId: string;
  providerVehicleTypeCode: string;
};

const rideHailingRoute: PRRoute = [
  {
    bd09: null,
    full_address: "杭州市上城区全福桥路2号",
    gcj02: [30.2912, 120.212],
    name: "杭州东站",
    wgs84: null,
  },
  {
    bd09: null,
    full_address: "杭州市西湖区灵隐路1号",
    gcj02: [30.24, 120.102],
    name: "灵隐寺",
    wgs84: null,
  },
];

const providerEstimatePricingModel: PricingModel = {
  type: "DYNAMIC_QUOTE",
  calculatorSpec: {
    components: [
      {
        amount: {
          path: "provider.estimateAmountFen",
          type: "INPUT",
        },
        id: "caocao-provider-estimate",
        label: "曹操预估价",
      },
    ],
    currency: "CNY",
    version: 1,
  },
};

const asCurrentSkuFacts = (facts: FutureRideHailingSkuFacts): SkuFacts =>
  facts as unknown as SkuFacts;

const readCaocaoCreateCount = (): number => matchedInteractionCount("caocao", "create-ride");

async function expireCommerceQuotes(): Promise<number> {
  const before = await db.select().from(commerceQuotes);
  await db.update(commerceQuotes).set({
    expiresAt: new Date(Date.now() - 1000),
  });
  return before.length;
}

async function waitForCommerceQuoteCountAtLeast(expected: number): Promise<void> {
  const deadline = Date.now() + 10_000;
  while (Date.now() < deadline) {
    const quotes = await db.select().from(commerceQuotes);
    if (quotes.length >= expected) return;
    await new Promise((resolve) => setTimeout(resolve, 100));
  }
  const quotes = await db.select().from(commerceQuotes);
  assert.ok(
    quotes.length >= expected,
    `Expected at least ${expected} commerce quotes, got ${quotes.length}`,
  );
}

async function waitForCaocaoCreateCount(expected: number): Promise<void> {
  const deadline = Date.now() + 10_000;
  while (Date.now() < deadline) {
    if (readCaocaoCreateCount() === expected) return;
    await new Promise((resolve) => setTimeout(resolve, 100));
  }
  assert.equal(readCaocaoCreateCount(), expected);
}

async function givenRideHailingPr(input: {
  creator: ScenarioUser;
  title: string;
}): Promise<ScenarioRideHailingPr> {
  const pr = await partnerRequestRepo.create({
    budget: null,
    createdBy: input.creator.user.id,
    joinGateConfig: [],
    location: null,
    maxPartners: null,
    meetingPoint: null,
    minPartners: 1,
    notes: null,
    preferences: ["安静"],
    route: rideHailingRoute,
    status: "OPEN",
    time: ["2031-04-01T02:00:00.000Z", "2031-04-01T03:00:00.000Z"],
    title: input.title,
    type: "ride-hailing-system-scenario",
  });
  if (!pr) {
    throw new Error("Failed to create RideHailing scenario PR");
  }

  await partnerRepo.createSlot({
    prId: pr.id,
    status: "JOINED",
    userId: input.creator.user.id,
  });

  return { id: pr.id };
}

async function registerScenarioPaymentProvider(): Promise<void> {
  const instanceKey = "system-svc-double-wechatpay-http-web";
  const register = async () => {
    const { weChatPayDouble } = getScenarioEnvironment();
    return registerPaymentProviderInstance({
    clientId: "web",
    config: {
      adapterMode: "WECHAT_PAY_API_V3",
      apiV3Key: weChatPayDouble.apiV3Key,
      appId: weChatPayDouble.appId,
      chargeMode: "JSAPI",
      endpointBaseUrl: weChatPayDouble.origin,
      mchId: weChatPayDouble.mchId,
      merchantCertificate: weChatPayDouble.merchantCertificate,
      platformCertificates: null,
    },
    displayName: "System SVC Double WeChatPay HTTP Web",
    instanceKey,
    providerType: "WECHAT_PAY",
  });
  };
  const registered = await register();
  await useWeChatPayDouble(registered.providerInstanceId);
  await register();
}

async function registerScenarioRideHailingProvider(instanceKey: string): Promise<{
  providerInstanceId: string;
}> {
  const { backendBaseUrl, caocaoDouble } = getScenarioEnvironment();
  return registerRideHailingProviderInstance({
    config: {
      adapterMode: "CAOCAO_OPEN_API",
      callbackBaseUrl: backendBaseUrl,
      caocaoClientId: caocaoDouble.clientId,
      endpointBaseUrl: caocaoDouble.origin,
      signKey: caocaoDouble.signKey,
    },
    displayName: "系统曹操",
    instanceKey,
    providerType: "CAOCAO",
  });
}

async function givenRideHailingOrderingPlacement(): Promise<{
  placementId: number;
  providerInstanceId: string;
  providerInstanceKey: string;
}> {
  const providerInstanceKey = `system-caocao-${randomUUID()}`;
  const provider = await registerScenarioRideHailingProvider(providerInstanceKey);

  const spu = await createProductSpu({
    name: "系统曹操出行",
    productType: "RIDE_HAILING",
    presentation: {
      detailImageAssetIds: [],
      heroImageAssetIds: [],
      noticeBlocks: [],
      parameterGroups: [],
      sellingPoints: ["曹操实时预估", "行程结束后按实际费用结算"],
    },
    salesPolicy: {
      quantityPolicy: {
        quantity: 1,
        type: "FIXED",
      },
      skuSelectionPolicy: {
        type: "CHOICE_SET",
        min: 1,
        max: null,
        resolvesTo: 1,
      },
    },
    servicePolicy: {
      type: "RIDE_HAILING",
    },
    status: "ACTIVE",
  });

  await productSkuRepo.create({
    facts: asCurrentSkuFacts({
      providerVehicleTypeCode: "3",
      rideHailingProviderInstanceId: provider.providerInstanceId,
    }),
    name: "快车",
    pricingModel: providerEstimatePricingModel,
    sortOrder: 10,
    spuId: spu.id,
    status: "ACTIVE",
  });

  await productSkuRepo.create({
    facts: asCurrentSkuFacts({
      providerVehicleTypeCode: "5",
      rideHailingProviderInstanceId: provider.providerInstanceId,
    }),
    name: "专车",
    pricingModel: providerEstimatePricingModel,
    sortOrder: 20,
    spuId: spu.id,
    status: "ACTIVE",
  });

  const offer = await createOffer({
    pricingRules: [],
    productType: "RIDE_HAILING",
    spuIds: [spu.id],
    status: "ACTIVE",
    termsVersion: 1,
  });

  const placement = await createPlacement({
    bindingRules: [
      {
        contextPath: "route",
        fieldKey: "route",
        lock: true,
      },
    ],
    creative: {
      ctaLabel: "叫曹操",
      description: "按当前路线预估网约车费用",
    },
    matchingRule: {
      and: [
        { "===": [{ var: "kind" }, "PR"] },
        { "===": [{ var: "type" }, "ride-hailing-system-scenario"] },
        {
          or: [{ "===": [{ var: "status" }, "READY"] }, { "===": [{ var: "status" }, "ACTIVE"] }],
        },
        { var: "hasRoute" },
        { var: "time.hasConcreteTime" },
      ],
    },
    placementType: "BUTTON",
    offerId: offer.id,
    priority: 100,
    status: "ACTIVE",
  });

  return {
    placementId: placement.id,
    providerInstanceId: provider.providerInstanceId,
    providerInstanceKey,
  };
}

async function assertLocatorTextIncludes(input: {
  actual: Promise<string | null>;
  expected: string;
  label: string;
}): Promise<void> {
  const actual = (await input.actual) ?? "";
  assert.ok(
    actual.includes(input.expected),
    `${input.label}: expected text to include "${input.expected}", got "${actual}"`,
  );
}

async function assertLocatorTextMatches(input: {
  actual: Promise<string | null>;
  pattern: RegExp;
  label: string;
}): Promise<void> {
  const actual = (await input.actual) ?? "";
  assert.match(actual, input.pattern, input.label);
}

async function waitForTextIncludes(input: {
  read: () => Promise<string | null>;
  expected: string;
  label: string;
  timeoutMs?: number;
}): Promise<void> {
  const timeoutMs = input.timeoutMs ?? 5_000;
  const startedAt = Date.now();
  let actual = "";

  while (Date.now() - startedAt < timeoutMs) {
    actual = (await input.read()) ?? "";
    if (actual.includes(input.expected)) {
      return;
    }
    await new Promise((resolve) => setTimeout(resolve, 200));
  }

  assert.ok(
    actual.includes(input.expected),
    `${input.label}: expected text to include "${input.expected}", got "${actual}"`,
  );
}

async function openRideHailingOrderingFromPr(input: { page: Page; prId: number }): Promise<void> {
  await input.page.goto(`/pr/${input.prId}`);
  await input.page.getByTestId("pr-detail.commerce-placement.open").click();
  await input.page.getByTestId("ordering.ride-hailing.page").waitFor({
    state: "visible",
    timeout: 10_000,
  });
}

const waitForOfferListingResponse = (page: Page): Promise<unknown> =>
  page.waitForResponse(
    (response) => {
      const url = new URL(response.url());
      return (
        response.request().method() === "POST" &&
        /^\/api\/commerce\/offers\/\d+\/listing$/.test(url.pathname) &&
        response.status() === 200
      );
    },
    { timeout: 10_000 },
  );

async function openRideHailingOrderingFromPrAndWaitForListing(input: {
  page: Page;
  prId: number;
}): Promise<void> {
  const listingResponse = waitForOfferListingResponse(input.page);
  await openRideHailingOrderingFromPr(input);
  await listingResponse;
}

async function waitForVehicleCardCount(page: Page, expected: number): Promise<void> {
  const vehicleCards = page.getByTestId("ordering.ride-hailing.vehicle-card");
  const deadline = Date.now() + 10_000;
  while (Date.now() < deadline) {
    if ((await vehicleCards.count()) === expected) return;
    await new Promise((resolve) => setTimeout(resolve, 100));
  }
  assert.equal(await vehicleCards.count(), expected);
}

async function assertRideHailingOrderingContent(page: Page): Promise<void> {
  await page.getByTestId("ordering.ride-hailing.route-map").waitFor({
    state: "visible",
    timeout: 10_000,
  });
  await page.getByTestId("ordering.ride-hailing.bottom-sheet").waitFor({
    state: "visible",
    timeout: 10_000,
  });
  await assertLocatorTextIncludes({
    actual: page.getByTestId("ordering.ride-hailing.departure-time").textContent(),
    label: "RideHailing departure row",
    expected: "现在出发",
  });
  await assertLocatorTextIncludes({
    actual: page.getByTestId("ordering.ride-hailing.riders").textContent(),
    expected: "同乘人",
    label: "RideHailing riders row",
  });
  await page.getByTestId("ordering.ride-hailing.price-detail.toggle").waitFor({
    state: "visible",
    timeout: 10_000,
  });
}

async function selectPremierAsAdditionalCandidate(page: Page): Promise<void> {
  const vehicleCards = page.getByTestId("ordering.ride-hailing.vehicle-card");
  await vehicleCards.first().waitFor({
    state: "visible",
    timeout: 10_000,
  });
  assert.equal(await vehicleCards.count(), 2);
  await vehicleCards.filter({ hasText: "系统曹操快车" }).waitFor({
    state: "visible",
    timeout: 10_000,
  });
  await vehicleCards.filter({ hasText: "系统曹操专车" }).waitFor({
    state: "visible",
    timeout: 10_000,
  });
  await assertLocatorTextMatches({
    actual: page.getByTestId("ordering.ride-hailing.quote-price-range").textContent(),
    label: "RideHailing default selected candidate price",
    pattern: /￥36\.00/,
  });
  await vehicleCards.filter({ hasText: "系统曹操专车" }).click();
  const selectedMarkers = page.getByTestId("ordering.ride-hailing.vehicle-card.selected");
  await selectedMarkers.first().waitFor({
    state: "visible",
    timeout: 10_000,
  });
  assert.equal(await selectedMarkers.count(), 2);
  await assertLocatorTextMatches({
    actual: page.getByTestId("ordering.ride-hailing.quote-price-range").textContent(),
    label: "RideHailing selected candidate range",
    pattern: /￥36\.00~52\.00/,
  });
}

async function assertRideHailingOrderDetail(
  page: Page,
  input: {
    expectedDispatchingVehicleLabels?: string[];
    expectedResolvedVehicleLabel?: string;
    expectedRiderNames?: string[];
    expectedStatusTitle?: string;
  } = {},
): Promise<void> {
  const expectedDispatchingVehicleLabels = input.expectedDispatchingVehicleLabels ?? [
    "系统曹操快车",
  ];
  const expectedRiderNames = input.expectedRiderNames ?? [];
  const expectedStatusTitle = input.expectedStatusTitle ?? "接客中";
  const expectedResolvedVehicleLabel =
    input.expectedResolvedVehicleLabel ??
    (expectedStatusTitle === "派单中" ? null : "系统曹操快车");

  await page.getByTestId("order-detail.page").waitFor({
    state: "visible",
    timeout: 10_000,
  });
  assert.match(new URL(page.url()).pathname, /^\/orders\/[0-9a-f-]+$/);
  await page.getByTestId("order-detail.ride-hailing.page").waitFor({
    state: "visible",
    timeout: 10_000,
  });
  await assertLocatorTextIncludes({
    actual: page.getByTestId("order-detail.ride-hailing.status-title").textContent(),
    expected: expectedStatusTitle,
    label: "RideHailing status hero title",
  });
  if (expectedStatusTitle === "派单中") {
    const dispatchingVehicleSection = page.getByTestId(
      "order-detail.ride-hailing.dispatching-skus",
    );
    await dispatchingVehicleSection.waitFor({
      state: "visible",
      timeout: 10_000,
    });
    const dispatchingVehicleCards = dispatchingVehicleSection.getByTestId(
      "order-detail.ride-hailing.vehicle-card",
    );
    assert.equal(await dispatchingVehicleCards.count(), expectedDispatchingVehicleLabels.length);
    for (const label of expectedDispatchingVehicleLabels) {
      await dispatchingVehicleCards.filter({ hasText: label }).waitFor({
        state: "visible",
        timeout: 10_000,
      });
    }
  }
  const resolvedVehicleSection = page.getByTestId(
    "order-detail.ride-hailing.resolved-vehicle-section",
  );
  if (expectedResolvedVehicleLabel === null) {
    await resolvedVehicleSection.waitFor({
      state: "hidden",
      timeout: 10_000,
    });
  } else {
    await resolvedVehicleSection.waitFor({
      state: "visible",
      timeout: 10_000,
    });
    const resolvedVehicleCards = resolvedVehicleSection.getByTestId(
      "order-detail.ride-hailing.vehicle-card",
    );
    assert.equal(await resolvedVehicleCards.count(), 1);
    await assertLocatorTextIncludes({
      actual: resolvedVehicleSection.textContent(),
      expected: "服务车型",
      label: "RideHailing resolved vehicle section title",
    });
    await assertLocatorTextIncludes({
      actual: resolvedVehicleSection.textContent(),
      expected: expectedResolvedVehicleLabel,
      label: "RideHailing resolved vehicle section item",
    });
  }
  await assertLocatorTextIncludes({
    actual: page.getByTestId("order-detail.ride-hailing.route-section").textContent(),
    expected: "杭州东站",
    label: "RideHailing route section origin",
  });
  await assertLocatorTextIncludes({
    actual: page.getByTestId("order-detail.ride-hailing.route-section").textContent(),
    expected: "灵隐寺",
    label: "RideHailing route section destination",
  });
  for (const expectedRiderName of expectedRiderNames) {
    await assertLocatorTextIncludes({
      actual: page.getByTestId("order-detail.ride-hailing.riders-section").textContent(),
      expected: expectedRiderName,
      label: `RideHailing riders section (${expectedRiderName})`,
    });
  }
}

async function assertRideHailingFactSectionOrder(input: {
  page: Page;
  before: string;
  after: string;
}): Promise<void> {
  const order = await input.page.evaluate(
    ({ after, before }) => {
      const beforeElement = document.querySelector<HTMLElement>(`[data-testid="${before}"]`);
      const afterElement = document.querySelector<HTMLElement>(`[data-testid="${after}"]`);
      if (!beforeElement || !afterElement) return null;
      const parent = beforeElement.parentElement;
      if (!parent || parent !== afterElement.parentElement) return null;
      return {
        afterIndex: Array.from(parent.children).indexOf(afterElement),
        beforeIndex: Array.from(parent.children).indexOf(beforeElement),
      };
    },
    { after: input.after, before: input.before },
  );
  assert.ok(order !== null, "RideHailing fact sections should share a common parent");
  assert.ok(
    order.beforeIndex >= 0 && order.beforeIndex < order.afterIndex,
    `Expected ${input.before} to appear before ${input.after}`,
  );
}

async function assertRideHailingBillCard(page: Page): Promise<void> {
  const billSection = page.getByTestId("order-detail.ride-hailing.bill-section");
  await billSection.waitFor({
    state: "visible",
    timeout: 10_000,
  });
  await assertLocatorTextIncludes({
    actual: billSection.textContent(),
    expected: "账单",
    label: "RideHailing bill section title",
  });
  await assertRideHailingFactSectionOrder({
    page,
    before: "order-detail.ride-hailing.bill-section",
    after: "order-detail.ride-hailing.resolved-vehicle-section",
  });
  await assertLocatorTextIncludes({
    actual: page.getByTestId("order-detail.ride-hailing.bill-card.status").textContent(),
    expected: "待支付",
    label: "RideHailing bill card status",
  });
  await assertLocatorTextMatches({
    actual: page.getByTestId("order-detail.ride-hailing.bill-card.amount").textContent(),
    pattern: /[¥￥]40\.00/,
    label: "RideHailing bill card amount",
  });
}

async function assertRideHailingBillDetailPage(input: {
  page: Page;
  viewerPayerName: string;
  otherPayerName: string;
  expectedBillStatus?: string;
  expectedViewerSettlementStatus?: string;
  expectedOtherSettlementStatus?: string;
  expectedViewerPayable?: boolean;
  expectedOtherPayable?: boolean;
  expectPayCta?: boolean;
  expectedViewerSelected?: boolean;
  expectedOtherSelected?: boolean;
}): Promise<void> {
  const { page } = input;
  const billLines = page.getByTestId("bill-detail.line");
  const expectedBillStatus = input.expectedBillStatus ?? "待支付";
  const expectedViewerSettlementStatus = input.expectedViewerSettlementStatus ?? "待支付";
  const expectedOtherSettlementStatus = input.expectedOtherSettlementStatus ?? "待支付";
  const expectedViewerPayable = input.expectedViewerPayable ?? true;
  const expectedOtherPayable = input.expectedOtherPayable ?? false;
  const expectPayCta = input.expectPayCta ?? true;
  const expectedViewerSelected = input.expectedViewerSelected ?? expectPayCta;
  const expectedOtherSelected = input.expectedOtherSelected ?? false;

  await page.getByTestId("bill-detail.page").waitFor({
    state: "visible",
    timeout: 10_000,
  });
  await waitForTextIncludes({
    read: () => page.getByTestId("bill-detail.status").textContent(),
    expected: expectedBillStatus,
    label: "RideHailing bill detail settlement status",
  });
  await assertLocatorTextIncludes({
    actual: page.getByTestId("bill-detail.status").textContent(),
    expected: expectedBillStatus,
    label: "RideHailing bill detail settlement status",
  });
  await assertLocatorTextMatches({
    actual: page.getByTestId("bill-detail.total-amount").textContent(),
    pattern: /总金额\s*[¥￥]40\.00/,
    label: "RideHailing bill detail total amount",
  });
  await billLines.first().waitFor({
    state: "visible",
    timeout: 10_000,
  });
  assert.equal(await billLines.count(), 2);

  const viewerLine = billLines.filter({ hasText: input.viewerPayerName });
  const otherLine = billLines.filter({ hasText: input.otherPayerName });

  await viewerLine.waitFor({
    state: "visible",
    timeout: 10_000,
  });
  await otherLine.waitFor({
    state: "visible",
    timeout: 10_000,
  });

  await assertLocatorTextIncludes({
    actual: viewerLine.getByTestId("bill-detail.line-payer").textContent(),
    expected: input.viewerPayerName,
    label: "RideHailing bill detail viewer payer",
  });
  await assertLocatorTextIncludes({
    actual: otherLine.getByTestId("bill-detail.line-payer").textContent(),
    expected: input.otherPayerName,
    label: "RideHailing bill detail other payer",
  });
  await assertLocatorTextMatches({
    actual: viewerLine.getByTestId("bill-detail.line-amount").textContent(),
    pattern: /[¥￥]20\.00/,
    label: "RideHailing bill detail viewer line amount",
  });
  await assertLocatorTextMatches({
    actual: otherLine.getByTestId("bill-detail.line-amount").textContent(),
    pattern: /[¥￥]20\.00/,
    label: "RideHailing bill detail other line amount",
  });

  const viewerLineControl = viewerLine.locator('[role="button"]');
  const otherLineControl = otherLine.locator('[role="button"]');

  await assertLocatorTextIncludes({
    actual: viewerLine.getByTestId("bill-detail.line-status").textContent(),
    expected: expectedViewerSettlementStatus,
    label: "RideHailing bill detail viewer line status",
  });
  await assertLocatorTextIncludes({
    actual: otherLine.getByTestId("bill-detail.line-status").textContent(),
    expected: expectedOtherSettlementStatus,
    label: "RideHailing bill detail other line status",
  });

  assert.equal(
    await viewerLine.getAttribute("data-payable"),
    expectedViewerPayable ? "true" : "false",
  );
  assert.equal(
    await viewerLine.getAttribute("data-selected"),
    expectedViewerSelected ? "true" : "false",
  );
  assert.equal(
    await viewerLineControl.getAttribute("aria-disabled"),
    expectedViewerPayable ? null : "true",
  );
  assert.equal(
    await otherLine.getAttribute("data-payable"),
    expectedOtherPayable ? "true" : "false",
  );
  assert.equal(
    await otherLine.getAttribute("data-selected"),
    expectedOtherSelected ? "true" : "false",
  );
  assert.equal(
    await otherLineControl.getAttribute("aria-disabled"),
    expectedOtherPayable ? null : "true",
  );

  if (expectPayCta) {
    await assertLocatorTextMatches({
      actual: page.getByTestId("bill-detail.pay-selected").textContent(),
      pattern: /支付\s*[¥￥]20\.00/,
      label: "RideHailing bill detail pay selected CTA",
    });
    return;
  }

  assert.equal(await page.getByTestId("bill-detail.pay-selected").count(), 0);
}

async function waitForRideHailingMapMode(
  page: Page,
  mode: "SEARCHING_ORIGIN" | "PICKING_UP" | "ARRIVED_AT_PICKUP" | "IN_TRIP" | "PLANNED_ROUTE",
): Promise<void> {
  await page
    .locator(`[data-testid="order-detail.ride-hailing.page"][data-map-mode="${mode}"]`)
    .waitFor({
      state: "visible",
      timeout: 10_000,
    });
}

scenario("commerce_ride_hailing_ordering_reaches_order_detail_for_active_pr", async (ctx) => {
  await useCaocaoDouble("default-multi");
  const creator = await givenUser("system-ride-hailing-creator", {
    phoneNumber: "13800138000",
  });
  const passenger = await givenUser("system-ride-hailing-passenger");
  await bindScenarioWeChatOpenId({
    openId: "fake-openid-commerce-ride-hailing-creator",
    user: creator,
  });
  const pr = await givenRideHailingPr({
    creator,
    title: "System ride hailing partner request",
  });
  await partnerRepo.createSlot({
    prId: pr.id,
    status: "JOINED",
    userId: passenger.user.id,
  });
  await configurePRStatus({ pr, status: "ACTIVE" });
  await registerScenarioPaymentProvider();
  const placement = await givenRideHailingOrderingPlacement();

  ctx.record("creatorUserId", creator.user.id);
  ctx.record("passengerUserId", passenger.user.id);
  ctx.record("prId", pr.id);
  ctx.record("placementId", placement.placementId);
  ctx.record("providerInstanceId", placement.providerInstanceId);

  let orderPath: string | null = null;

  await withScenarioPage(async (page) => {
    await installScenarioUserSession(page, creator);
    await installDeterministicShareSidecarStubs(page);
    await installWeChatPayDoubleBridge(page);

    await openRideHailingOrderingFromPr({ page, prId: pr.id });
    await assertRideHailingOrderingContent(page);
    await selectPremierAsAdditionalCandidate(page);

    await page.getByTestId("ordering.ride-hailing.create-order").click();
    await page.getByTestId("order-detail.page").waitFor({ state: "visible", timeout: 10_000 });
    emitCaocaoEvent("order.accepted");
    await waitForRideHailingMapMode(page, "PICKING_UP");
    await assertRideHailingOrderDetail(page, {
      expectedDispatchingVehicleLabels: ["系统曹操快车", "系统曹操专车"],
      expectedRiderNames: [
        "scenario-system-ride-hailing-creator",
        "scenario-system-ride-hailing-passenger",
      ],
    });
    assert.equal(readCaocaoCreateCount(), 1);

    await assertLocatorTextIncludes({
      actual: page.getByTestId("order-detail.ride-hailing.status-title").textContent(),
      expected: "接客中",
      label: "RideHailing accepted status hero",
    });
    await assertRideHailingOrderDetail(page, {
      expectedRiderNames: [
        "scenario-system-ride-hailing-creator",
        "scenario-system-ride-hailing-passenger",
      ],
    });
    const driverCard = page.getByTestId("order-detail.ride-hailing.driver-card");
    await driverCard.waitFor({
      state: "visible",
      timeout: 10_000,
    });
    await assertLocatorTextIncludes({
      actual: driverCard.textContent(),
      expected: "曹操测试司机",
      label: "RideHailing driver card driver name",
    });
    await assertLocatorTextIncludes({
      actual: driverCard.textContent(),
      expected: "浙A12345",
      label: "RideHailing driver card vehicle plate",
    });

    emitCaocaoEvent("order.arrived");
    await waitForRideHailingMapMode(page, "ARRIVED_AT_PICKUP");

    emitCaocaoEvent("order.in-trip");
    await waitForRideHailingMapMode(page, "IN_TRIP");

    emitCaocaoEvent("order.finished");
    await waitForRideHailingMapMode(page, "PLANNED_ROUTE");
    await assertLocatorTextIncludes({
      actual: page.getByTestId("order-detail.ride-hailing.status-title").textContent(),
      expected: "行程已结束",
      label: "RideHailing finished status hero",
    });
    await assertRideHailingBillCard(page);

    const orderDetailPath = new URL(page.url()).pathname;
    orderPath = orderDetailPath;
    await page.goBack();
    await page.waitForURL((url) => new URL(url).pathname === `/pr/${pr.id}`, {
      timeout: 10_000,
    });
    await page.goto(orderDetailPath);
    await page.getByTestId("order-detail.page").waitFor({
      state: "visible",
      timeout: 10_000,
    });
    await page.getByTestId("order-detail.ride-hailing.bill-card.view").click();
    await page.waitForURL((url) => /^\/bills\/[0-9a-f-]+$/.test(new URL(url).pathname), {
      timeout: 10_000,
    });
    const billDetailPath = new URL(page.url()).pathname;
    await assertRideHailingBillDetailPage({
      page,
      viewerPayerName: "scenario-system-ride-hailing-creator",
      otherPayerName: "scenario-system-ride-hailing-passenger",
    });
    await page.getByTestId("bill-detail.pay-selected").click();
    await page.waitForURL(
      (url) => {
        const checkoutUrl = new URL(url);
        return (
          checkoutUrl.pathname === "/payment/checkout" &&
          /^[0-9a-f-]+$/.test(checkoutUrl.searchParams.get("bill-line") ?? "")
        );
      },
      {
        timeout: 10_000,
      },
    );
    await page.getByTestId("payment-checkout.page").waitFor({
      state: "visible",
      timeout: 10_000,
    });
    await page.getByTestId("payment-checkout.pay").click();
    await page.waitForURL((url) => new URL(url).pathname === billDetailPath, {
      timeout: 15_000,
    });
    await assertRideHailingBillDetailPage({
      page,
      viewerPayerName: "scenario-system-ride-hailing-creator",
      otherPayerName: "scenario-system-ride-hailing-passenger",
      expectedBillStatus: "部分已支付",
      expectedViewerSettlementStatus: "已支付",
      expectedOtherSettlementStatus: "待支付",
      expectedViewerPayable: false,
      expectPayCta: false,
      expectedViewerSelected: false,
    });
    await page.getByTestId("bill-detail.order-link").click();
    await page.waitForURL((url) => new URL(url).pathname === orderDetailPath, {
      timeout: 10_000,
    });
    await page.getByTestId("order-detail.page").waitFor({
      state: "visible",
      timeout: 10_000,
    });
  });

  const createdOrderPath = orderPath;
  assert.match(createdOrderPath ?? "", /^\/orders\/[0-9a-f-]+$/);
});

scenario("commerce_ride_hailing_placement_entry_uses_backend_admission", async (ctx) => {
  await useCaocaoDouble("default-multi");
  const creator = await givenUser("system-placement-admission-creator", {
    phoneNumber: "13800138009",
  });
  const participant = await givenUser("system-placement-admission-participant");
  const pr = await givenRideHailingPr({
    creator,
    title: "System Placement admission PR",
  });
  await partnerRepo.createSlot({
    prId: pr.id,
    status: "JOINED",
    userId: participant.user.id,
  });
  await configurePRStatus({ pr, status: "READY" });
  await registerScenarioPaymentProvider();
  const placement = await givenRideHailingOrderingPlacement();

  ctx.record("creatorUserId", creator.user.id);
  ctx.record("participantUserId", participant.user.id);
  ctx.record("prId", pr.id);
  ctx.record("placementId", placement.placementId);

  await withScenarioPage(async (page) => {
    await installScenarioUserSession(page, participant);
    await installDeterministicShareSidecarStubs(page);

    await page.goto(`/pr/${pr.id}`);
    await page.getByTestId("pr-detail.commerce-placement.open").click();
    await page.getByTestId("pr-detail.commerce-placement.admission-result").waitFor({
      state: "visible",
      timeout: 10_000,
    });
    await assertLocatorTextIncludes({
      actual: page.getByTestId("pr-detail.commerce-placement.admission-result").textContent(),
      expected: "仅搭子发起人可以创建新订单",
      label: "non-creator Placement admission result",
    });
    assert.equal(new URL(page.url()).pathname, `/pr/${pr.id}`);
  });

  let createdOrderPath = "";
  await withScenarioPage(async (page) => {
    await installScenarioUserSession(page, creator);
    await installDeterministicShareSidecarStubs(page);

    await openRideHailingOrderingFromPr({ page, prId: pr.id });
    assert.equal(new URL(page.url()).pathname, "/order/new");
    await selectPremierAsAdditionalCandidate(page);
    await page.getByTestId("ordering.ride-hailing.create-order").click();
    await page.getByTestId("order-detail.page").waitFor({ state: "visible", timeout: 10_000 });
    emitCaocaoEvent("order.accepted");
    await waitForRideHailingMapMode(page, "PICKING_UP");
    await assertRideHailingOrderDetail(page);
    createdOrderPath = new URL(page.url()).pathname;
  });
  assert.match(createdOrderPath, /^\/orders\/[0-9a-f-]+$/);

  await withScenarioPage(async (page) => {
    await installScenarioUserSession(page, participant);
    await installDeterministicShareSidecarStubs(page);

    await page.goto(`/pr/${pr.id}`);
    await page.getByTestId("pr-detail.commerce-placement.open").click();
    await page.waitForURL((url) => new URL(url).pathname === createdOrderPath, {
      timeout: 10_000,
    });
    await page.getByTestId("order-detail.page").waitFor({
      state: "visible",
      timeout: 10_000,
    });
  });
});

scenario("commerce_ride_hailing_order_detail_cancel_dispatching_order", async (ctx) => {
  await useCaocaoDouble("cancel-zero");
  const creator = await givenUser("system-ride-hailing-cancel-creator", {
    phoneNumber: "13800138006",
  });
  await bindScenarioWeChatOpenId({
    openId: "fake-openid-commerce-ride-hailing-cancel-creator",
    user: creator,
  });
  const pr = await givenRideHailingPr({
    creator,
    title: "System ride hailing cancel PR",
  });
  await configurePRStatus({ pr, status: "READY" });
  await registerScenarioPaymentProvider();
  const placement = await givenRideHailingOrderingPlacement();

  ctx.record("creatorUserId", creator.user.id);
  ctx.record("prId", pr.id);
  ctx.record("placementId", placement.placementId);
  ctx.record("providerInstanceId", placement.providerInstanceId);

  await withScenarioPage(async (page) => {
    await installScenarioUserSession(page, creator);
    await installDeterministicShareSidecarStubs(page);

    await openRideHailingOrderingFromPr({ page, prId: pr.id });
    await assertRideHailingOrderingContent(page);
    await page.getByTestId("ordering.ride-hailing.create-order").click();
    await assertRideHailingOrderDetail(page, {
      expectedDispatchingVehicleLabels: ["系统曹操快车"],
      expectedResolvedVehicleLabel: undefined,
      expectedStatusTitle: "派单中",
    });
    await waitForCaocaoCreateCount(1);

    await page.getByTestId("order-detail.ride-hailing.cancel").click();
    await waitForTextIncludes({
      read: () => page.getByTestId("order-detail.ride-hailing.status-title").textContent(),
      expected: "已取消",
      label: "RideHailing cancelled status hero",
    });
    assert.equal(await page.getByTestId("order-detail.ride-hailing.cancel").count(), 0);
  });
});

scenario("commerce_ride_hailing_order_detail_prompts_positive_cancel_fee", async (ctx) => {
  await useCaocaoDouble("default-single");
  const creator = await givenUser("system-ride-hailing-cancel-fee-creator", {
    phoneNumber: "13800138007",
  });
  await bindScenarioWeChatOpenId({
    openId: "fake-openid-commerce-ride-hailing-cancel-fee-creator",
    user: creator,
  });
  const pr = await givenRideHailingPr({
    creator,
    title: "System ride hailing cancel fee PR",
  });
  await configurePRStatus({ pr, status: "READY" });
  await registerScenarioPaymentProvider();
  const placement = await givenRideHailingOrderingPlacement();

  ctx.record("creatorUserId", creator.user.id);
  ctx.record("prId", pr.id);
  ctx.record("placementId", placement.placementId);
  ctx.record("providerInstanceId", placement.providerInstanceId);

  await withScenarioPage(async (page) => {
    await installScenarioUserSession(page, creator);
    await installDeterministicShareSidecarStubs(page);

    await openRideHailingOrderingFromPr({ page, prId: pr.id });
    await assertRideHailingOrderingContent(page);
    await page.getByTestId("ordering.ride-hailing.create-order").click();
    await page.getByTestId("order-detail.page").waitFor({ state: "visible", timeout: 10_000 });
    emitCaocaoEvent("order.accepted");
    await waitForRideHailingMapMode(page, "PICKING_UP");
    await assertRideHailingOrderDetail(page);
    await waitForCaocaoCreateCount(1);

    await page.getByTestId("order-detail.ride-hailing.cancel").click();
    await page.getByTestId("order-detail.ride-hailing.cancel-confirm").waitFor({
      state: "visible",
      timeout: 10_000,
    });
    await assertLocatorTextMatches({
      actual: page.getByTestId("order-detail.ride-hailing.cancel-fee").textContent(),
      pattern: /[¥￥]8\.00/,
      label: "RideHailing positive cancellation fee preview",
    });

    await page.getByTestId("order-detail.ride-hailing.cancel-confirm.confirm").click();
    await waitForTextIncludes({
      read: () => page.getByTestId("order-detail.ride-hailing.status-title").textContent(),
      expected: "已取消",
      label: "RideHailing positive-fee cancelled status hero",
    });
  });
});

scenario("commerce_ride_hailing_provider_create_failure_stays_on_ordering_page", async (ctx) => {
  await useCaocaoDouble("create-failure");
  const creator = await givenUser("system-ride-hailing-failure-creator", {
    phoneNumber: "13800138000",
  });
  const pr = await givenRideHailingPr({
    creator,
    title: "System ride hailing provider failure PR",
  });
  await configurePRStatus({ pr, status: "READY" });
  await registerScenarioPaymentProvider();
  const placement = await givenRideHailingOrderingPlacement();

  ctx.record("creatorUserId", creator.user.id);
  ctx.record("prId", pr.id);
  ctx.record("placementId", placement.placementId);

  await withScenarioPage(async (page) => {
    await installScenarioUserSession(page, creator);
    await installDeterministicShareSidecarStubs(page);

    await openRideHailingOrderingFromPr({ page, prId: pr.id });
    await selectPremierAsAdditionalCandidate(page);
    await page.getByTestId("ordering.ride-hailing.create-order").click();
    await page.getByTestId("ordering.ride-hailing.page").waitFor({
      state: "visible",
      timeout: 10_000,
    });
    await page.getByText("下单失败").waitFor({
      state: "visible",
      timeout: 10_000,
    });
    await assertLocatorTextIncludes({
      actual: page.locator("body").textContent(),
      expected: "Fake Caocao create failed",
      label: "RideHailing create failure dialog",
    });
    assert.equal(new URL(page.url()).pathname, "/order/new");
  });
});

scenario("commerce_ride_hailing_unavailable_provider_vehicle_is_hidden", async (ctx) => {
  await useCaocaoDouble("unavailable-5");
  const creator = await givenUser("system-ride-hailing-unavailable-vehicle-creator", {
    phoneNumber: "13800138003",
  });
  await bindScenarioWeChatOpenId({
    openId: "fake-openid-commerce-ride-hailing-unavailable-vehicle-creator",
    user: creator,
  });
  const pr = await givenRideHailingPr({
    creator,
    title: "System ride hailing unavailable vehicle PR",
  });
  await configurePRStatus({ pr, status: "READY" });
  await registerScenarioPaymentProvider();
  const placement = await givenRideHailingOrderingPlacement();

  ctx.record("creatorUserId", creator.user.id);
  ctx.record("prId", pr.id);
  ctx.record("placementId", placement.placementId);

  await withScenarioPage(async (page) => {
    await installScenarioUserSession(page, creator);
    await installDeterministicShareSidecarStubs(page);

    await openRideHailingOrderingFromPrAndWaitForListing({ page, prId: pr.id });
    await assertRideHailingOrderingContent(page);

    await waitForVehicleCardCount(page, 1);
    await page
      .getByTestId("ordering.ride-hailing.vehicle-card")
      .filter({
        hasText: "系统曹操快车",
      })
      .waitFor({
        state: "visible",
        timeout: 10_000,
      });
    await page
      .getByTestId("ordering.ride-hailing.vehicle-card")
      .filter({
        hasText: "系统曹操专车",
      })
      .waitFor({
        state: "hidden",
        timeout: 10_000,
      });
    await assertLocatorTextMatches({
      actual: page.getByTestId("ordering.ride-hailing.quote-price-range").textContent(),
      label: "RideHailing only available candidate price",
      pattern: /￥36\.00/,
    });

    await page.getByTestId("ordering.ride-hailing.create-order").click();
    await page.getByTestId("order-detail.page").waitFor({ state: "visible", timeout: 10_000 });
    emitCaocaoEvent("order.accepted");
    await waitForRideHailingMapMode(page, "PICKING_UP");
    await assertRideHailingOrderDetail(page);
    assert.equal(readCaocaoCreateCount(), 1);
  });
});

scenario("commerce_ride_hailing_quote_expired_refreshes_and_preserves_selection", async (ctx) => {
  await useCaocaoDouble("default-multi");
  const creator = await givenUser("system-ride-hailing-quote-expired-creator", {
    phoneNumber: "13800138002",
  });
  await bindScenarioWeChatOpenId({
    openId: "fake-openid-commerce-ride-hailing-quote-expired-creator",
    user: creator,
  });
  const pr = await givenRideHailingPr({
    creator,
    title: "System ride hailing quote expired PR",
  });
  await configurePRStatus({ pr, status: "READY" });
  await registerScenarioPaymentProvider();
  const placement = await givenRideHailingOrderingPlacement();

  ctx.record("creatorUserId", creator.user.id);
  ctx.record("prId", pr.id);
  ctx.record("placementId", placement.placementId);
  ctx.record("providerInstanceId", placement.providerInstanceId);

  await withScenarioPage(async (page) => {
    await installScenarioUserSession(page, creator);
    await installDeterministicShareSidecarStubs(page);

    await openRideHailingOrderingFromPr({ page, prId: pr.id });
    await assertRideHailingOrderingContent(page);
    await selectPremierAsAdditionalCandidate(page);

    const quoteCountBeforeExpire = await expireCommerceQuotes();

    await page.getByTestId("ordering.ride-hailing.create-order").click();
    await page.getByRole("heading", { name: "报价已过期" }).waitFor({
      state: "visible",
      timeout: 10_000,
    });
    assert.equal(readCaocaoCreateCount(), 0);
    await waitForCommerceQuoteCountAtLeast(quoteCountBeforeExpire + 2);
    await page.getByRole("button", { name: "我知道了" }).click();

    const selectedMarkers = page.getByTestId("ordering.ride-hailing.vehicle-card.selected");
    await selectedMarkers.first().waitFor({
      state: "visible",
      timeout: 10_000,
    });
    assert.equal(await selectedMarkers.count(), 2);
    await page.getByTestId("ordering.ride-hailing.create-order").click();
    await page.getByTestId("order-detail.page").waitFor({ state: "visible", timeout: 10_000 });
    emitCaocaoEvent("order.accepted");
    await waitForRideHailingMapMode(page, "PICKING_UP");
    await assertRideHailingOrderDetail(page, {
      expectedDispatchingVehicleLabels: ["系统曹操快车", "系统曹操专车"],
    });
    assert.equal(readCaocaoCreateCount(), 1);
  });
});

scenario("commerce_ride_hailing_quote_refresh_prunes_unavailable_selected_vehicle", async (ctx) => {
  await useCaocaoDouble("default-multi");
  const creator = await givenUser("system-ride-hailing-quote-prune-creator", {
    phoneNumber: "13800138004",
  });
  await bindScenarioWeChatOpenId({
    openId: "fake-openid-commerce-ride-hailing-quote-prune-creator",
    user: creator,
  });
  const pr = await givenRideHailingPr({
    creator,
    title: "System ride hailing quote prune PR",
  });
  await configurePRStatus({ pr, status: "READY" });
  await registerScenarioPaymentProvider();
  const placement = await givenRideHailingOrderingPlacement();

  ctx.record("creatorUserId", creator.user.id);
  ctx.record("prId", pr.id);
  ctx.record("placementId", placement.placementId);
  ctx.record("providerInstanceId", placement.providerInstanceId);

  await withScenarioPage(async (page) => {
    await installScenarioUserSession(page, creator);
    await installDeterministicShareSidecarStubs(page);

    await openRideHailingOrderingFromPr({ page, prId: pr.id });
    await assertRideHailingOrderingContent(page);
    await selectPremierAsAdditionalCandidate(page);

    const quoteCountBeforeExpire = await expireCommerceQuotes();
    await useCaocaoDouble("unavailable-5");
    await registerScenarioRideHailingProvider(placement.providerInstanceKey);

    await page.getByTestId("ordering.ride-hailing.create-order").click();
    await page.getByRole("heading", { name: "报价已过期" }).waitFor({
      state: "visible",
      timeout: 10_000,
    });
    assert.equal(readCaocaoCreateCount(), 0);
    await waitForCommerceQuoteCountAtLeast(quoteCountBeforeExpire + 1);
    await page.getByRole("button", { name: "我知道了" }).click();

    await waitForVehicleCardCount(page, 1);
    await page
      .getByTestId("ordering.ride-hailing.vehicle-card")
      .filter({
        hasText: "系统曹操专车",
      })
      .waitFor({
        state: "hidden",
        timeout: 10_000,
      });
    const selectedMarkers = page.getByTestId("ordering.ride-hailing.vehicle-card.selected");
    await selectedMarkers.first().waitFor({
      state: "visible",
      timeout: 10_000,
    });
    assert.equal(await selectedMarkers.count(), 1);
    await assertLocatorTextMatches({
      actual: page.getByTestId("ordering.ride-hailing.quote-price-range").textContent(),
      label: "RideHailing pruned candidate price",
      pattern: /￥36\.00/,
    });

    await page.getByTestId("ordering.ride-hailing.create-order").click();
    await page.getByTestId("order-detail.page").waitFor({ state: "visible", timeout: 10_000 });
    emitCaocaoEvent("order.accepted");
    await waitForRideHailingMapMode(page, "PICKING_UP");
    await assertRideHailingOrderDetail(page);
    assert.equal(readCaocaoCreateCount(), 1);
  });
});

scenario("commerce_ride_hailing_all_provider_vehicles_unavailable_blocks_ordering", async (ctx) => {
  await useCaocaoDouble("unavailable-all");
  const creator = await givenUser("system-ride-hailing-no-vehicles-creator", {
    phoneNumber: "13800138005",
  });
  await bindScenarioWeChatOpenId({
    openId: "fake-openid-commerce-ride-hailing-no-vehicles-creator",
    user: creator,
  });
  const pr = await givenRideHailingPr({
    creator,
    title: "System ride hailing no vehicles PR",
  });
  await configurePRStatus({ pr, status: "READY" });
  await registerScenarioPaymentProvider();
  const placement = await givenRideHailingOrderingPlacement();

  ctx.record("creatorUserId", creator.user.id);
  ctx.record("prId", pr.id);
  ctx.record("placementId", placement.placementId);

  await withScenarioPage(async (page) => {
    await installScenarioUserSession(page, creator);
    await installDeterministicShareSidecarStubs(page);

    await openRideHailingOrderingFromPrAndWaitForListing({ page, prId: pr.id });
    await assertRideHailingOrderingContent(page);
    await waitForVehicleCardCount(page, 0);
    await assertLocatorTextIncludes({
      actual: page.getByTestId("ordering.ride-hailing.quote-price-range").textContent(),
      expected: "待确认",
      label: "RideHailing unavailable candidate price",
    });
    assert.equal(await page.getByTestId("ordering.ride-hailing.create-order").isDisabled(), true);
    assert.equal(readCaocaoCreateCount(), 0);
  });
});
