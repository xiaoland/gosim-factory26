import assert from "node:assert/strict";
import { randomUUID } from "node:crypto";
import {
  createOffer,
  createProductSku,
  createProductSpu,
} from "../../../apps/backend/src/domains/merchandising/commands";
import { bills } from "../../../apps/backend/src/entities/bill";
import {
  commerceQuotes,
  type OfferListingSessionId,
  type OfferQuoteId,
} from "../../../apps/backend/src/entities/commerce-quote";
import { createOrderAttempts } from "../../../apps/backend/src/entities/create-order-attempt";
import { rentalOrders } from "../../../apps/backend/src/entities/rental-order";
import { tradeOrders } from "../../../apps/backend/src/entities/trade-order";
import { db } from "../../../apps/backend/src/lib/db";
import { CommerceQuoteRepository } from "../../../apps/backend/src/repositories/CommerceQuoteRepository";
import { givenAdminUser, givenUser } from "../../../apps/backend/tests/pr/_kit/builders/users";
import { expectBackendJsonResponse, requestBackendJson } from "../_infra/http/backend";
import { doubleJournalTotal } from "../_infra/double/scenario-doubles";
import { scenario } from "../_infra/scenario/scenario";

const RETIRED_CODE = "RENTAL_RUNTIME_RETIRED";
const RETIRED_TYPE = "https://partner-up.app/problems/commerce.rental-runtime-retired";
const serviceStartAt = "2031-06-01T10:00:00.000Z";
const serviceEndAt = "2031-06-01T12:00:00.000Z";

type RentalRetiredProblem = {
  type: string;
  title: string;
  status: number;
  detail: string;
  code: string;
};

type RuntimeEffectSnapshot = {
  quoteCount: number;
  orderCount: number;
  billCount: number;
  rentalOrderCount: number;
  createOrderAttemptCount: number;
  weChatBoundaryJournalCount: number;
  caocaoBoundaryJournalCount: number;
};

const expectRentalRetired = async (response: Response): Promise<RentalRetiredProblem> => {
  const problem = await expectBackendJsonResponse<RentalRetiredProblem>(response, 410);
  assert.equal(problem.status, 410);
  assert.equal(problem.code, RETIRED_CODE);
  assert.equal(problem.type, RETIRED_TYPE);
  return problem;
};

const readRuntimeEffectSnapshot = async (): Promise<RuntimeEffectSnapshot> => {
  const [quoteRows, orderRows, billRows, rentalOrderRows, createOrderAttemptRows] =
    await Promise.all([
    db.select({ id: commerceQuotes.id }).from(commerceQuotes),
    db.select({ id: tradeOrders.id }).from(tradeOrders),
    db.select({ id: bills.id }).from(bills),
    db.select({ id: rentalOrders.orderId }).from(rentalOrders),
    db.select({ id: createOrderAttempts.id }).from(createOrderAttempts),
  ]);

  return {
    quoteCount: quoteRows.length,
    orderCount: orderRows.length,
    billCount: billRows.length,
    rentalOrderCount: rentalOrderRows.length,
    createOrderAttemptCount: createOrderAttemptRows.length,
    weChatBoundaryJournalCount: doubleJournalTotal("wechatpay"),
    caocaoBoundaryJournalCount: doubleJournalTotal("caocao"),
  };
};

scenario(
  "commerce_rental_runtime_retirement_rejects_public_writes_without_effects",
  async (ctx) => {
    const customer = await givenUser(`rental-retired-customer-${randomUUID()}`);
    const operator = await givenAdminUser(`rental-retired-operator-${randomUUID()}`);
    const spu = await createProductSpu({
      name: `Retired Rental ${randomUUID()}`,
      productType: "RENTAL",
      status: "ACTIVE",
      salesPolicy: {
        skuSelectionPolicy: { type: "EXACTLY_ONE" },
        quantityPolicy: { type: "FIXED", quantity: 1 },
      },
      servicePolicy: {
        type: "RENTAL",
        bookingLeadTimeMinutes: 0,
        requiresContactPhone: true,
        requiresRealName: true,
        requiresNationalId: false,
      },
      presentation: {
        heroImageAssetIds: [],
        detailImageAssetIds: [],
        sellingPoints: [],
        parameterGroups: [],
        noticeBlocks: [],
      },
    });
    const sku = await createProductSku({
      spuId: spu.id,
      name: "Retired Rental SKU",
      status: "ACTIVE",
      facts: {
        type: "RENTAL",
        zoneCode: `RETIRED_${randomUUID()}`,
        participantCount: 1,
        durationMinutes: 120,
      },
      pricingModel: {
        type: "FIXED_TOTAL",
        amountFen: 1200,
      },
    });
    const offer = await createOffer({
      productType: "RENTAL",
      spuIds: [spu.id],
      status: "ACTIVE",
      pricingRules: [],
      termsVersion: 1,
    });

    const beforeListing = await readRuntimeEffectSnapshot();
    const listingProblem = await expectRentalRetired(
      await requestBackendJson(`/api/commerce/offers/${offer.id}/listing`, {
        method: "POST",
        token: customer.token,
        body: {
          productType: "RENTAL",
          participants: [
            {
              userId: customer.user.id,
              displayName: customer.user.nickname,
              phoneMasked: null,
            },
          ],
          serviceStartAt,
          serviceEndAt,
          contactPhone: "13800138000",
          registrants: [{ fullName: "退役租赁测试" }],
        },
      }),
    );
    assert.deepEqual(await readRuntimeEffectSnapshot(), beforeListing);

    const quoteId = randomUUID() as OfferQuoteId;
    await new CommerceQuoteRepository().create({
      id: quoteId,
      listingSessionId: randomUUID() as OfferListingSessionId,
      offerId: offer.id,
      productType: "RENTAL",
      itemKind: "FIXED",
      spuId: spu.id,
      skuId: sku.id,
      quantity: 1,
      listingContextSnapshot: {
        productType: "RENTAL",
        participants: [
          {
            participantId: randomUUID(),
            userId: customer.user.id,
            role: "CREATOR",
            joinedVia: "API",
            joinedAt: new Date().toISOString(),
            removedAt: null,
          },
        ],
        serviceStartAt,
        serviceEndAt,
        contactPhone: "13800138000",
        registrants: [
          {
            name: "退役租赁测试",
            phone: "13800138000",
            nationalIdMasked: null,
          },
        ],
      },
      fulfillmentQuoteSnapshot: { productType: "RENTAL" },
      pricingSnapshot: {
        currency: "CNY",
        totalFen: 1200,
        explanations: [],
      },
      expiresAt: new Date(Date.now() + 5 * 60 * 1000),
    });

    const beforeRejectedWrites = await readRuntimeEffectSnapshot();
    const createProblem = await expectRentalRetired(
      await requestBackendJson("/api/commerce/orders", {
        method: "POST",
        token: customer.token,
        headers: { "idempotency-key": randomUUID() },
        body: {
          items: [{ kind: "FIXED", quoteId, quantity: 1 }],
        },
      }),
    );

    const missingFulfillmentId = randomUUID();
    const customerFulfillmentProblem = await expectRentalRetired(
      await requestBackendJson(
        `/api/commerce/orders/${missingFulfillmentId}/mock-rental-booking-confirmation`,
        {
          method: "POST",
          token: customer.token,
        },
      ),
    );
    const adminFulfillmentProblem = await expectRentalRetired(
      await requestBackendJson(
        `/api/admin/commerce/fulfillments/rental/${missingFulfillmentId}/confirm-booking`,
        {
          method: "POST",
          token: operator.token,
          body: { bookingNote: "must stay retired" },
        },
      ),
    );

    const afterRejectedWrites = await readRuntimeEffectSnapshot();
    assert.deepEqual(afterRejectedWrites, beforeRejectedWrites);

    ctx.record("offerId", offer.id);
    ctx.record("quoteId", quoteId);
    ctx.record("listingProblemCode", listingProblem.code);
    ctx.record("createProblemCode", createProblem.code);
    ctx.record("customerFulfillmentProblemCode", customerFulfillmentProblem.code);
    ctx.record("adminFulfillmentProblemCode", adminFulfillmentProblem.code);
    ctx.record("beforeRejectedWrites", beforeRejectedWrites);
    ctx.record("afterRejectedWrites", afterRejectedWrites);
  },
);
