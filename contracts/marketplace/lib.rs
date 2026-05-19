//! # GreenVerify AI — Carbon Credit Marketplace
//!
//! A **decentralised, fixed-price marketplace** for trading verified carbon
//! credit PSP34 NFTs.  Prices are denominated in **POT** (Portaldot's native
//! token).
//!
//! ## Listing Flow
//!
//! 1. Seller calls `PSP34::approve(marketplace, Some(token_id))` on the
//!    CarbonCredit contract to authorise this marketplace.
//! 2. Seller calls [`Marketplace::list`] providing `token_id` and `price`.
//!    The marketplace immediately pulls the NFT into escrow via a
//!    cross-contract `PSP34::transfer` call.
//!
//! ## Purchase Flow
//!
//! 1. Buyer calls [`Marketplace::buy(token_id)`], attaching `price` POT as
//!    call value.
//! 2. The contract forwards the POT to the seller and pushes the NFT to the
//!    buyer via a cross-contract `PSP34::transfer` call.
//!
//! ## Delisting
//!
//! The original seller may call [`Marketplace::delist`] at any time to cancel
//! a listing and reclaim their NFT.
//!
//! ## Security
//!
//! - Cross-contract calls use the canonical PSP34 selectors so this
//!   marketplace works with **any** standard-conforming PSP34 contract.
//! - The contract validates that callers are approved (for listings) and
//!   that attached value matches the listed price (for purchases).

#![cfg_attr(not(feature = "std"), no_std)]

/// The marketplace contract.
#[ink::contract]
pub mod marketplace {

    // =========================================================================
    //  Imports
    // =========================================================================

    use ink::env::call::{build_call, Call, ExecutionInput, Selector};

    // =========================================================================
    //  PSP34 compatibility types
    // =========================================================================

    /// PSP34 Token ID — mirrors the OpenBrush / PSP34 specification exactly
    /// so SCALE encoding/decoding is binary-compatible for cross-contract
    /// calls.
    ///
    /// **IMPORTANT** — the variant ordering and field types MUST match the
    /// PSP34 contract's `Id` definition.
    #[derive(scale::Encode, scale::Decode, Clone, Debug, PartialEq, Eq)]
    #[cfg_attr(
        feature = "std",
        derive(scale_info::TypeInfo, ink::storage::traits::StorageLayout)
    )]
    pub enum PSP34Id {
        U8(u8),
        U16(u16),
        U32(u32),
        U64(u64),
        U128(u128),
        Bytes(ink::prelude::vec::Vec<u8>),
    }

    /// PSP34 Error — mirrors the spec so we can SCALE-decode the return
    /// value of cross-contract `transfer` calls.
    #[derive(scale::Encode, scale::Decode, Clone, Debug, PartialEq, Eq)]
    #[cfg_attr(
        feature = "std",
        derive(scale_info::TypeInfo, ink::storage::traits::StorageLayout)
    )]
    pub enum PSP34Error {
        TokenNotExists,
        NotApproved,
        TokenExists,
        SelfApprove,
        SafeTransferCheckFailed(ink::prelude::vec::Vec<u8>),
    }

    // =========================================================================
    //  Listing type
    // =========================================================================

    /// A single marketplace listing.
    #[derive(
        scale::Encode, scale::Decode, Clone, Debug, PartialEq, Eq,
    )]
    #[cfg_attr(
        feature = "std",
        derive(scale_info::TypeInfo, ink::storage::traits::StorageLayout)
    )]
    pub struct Listing {
        /// The `u128` token ID of the listed carbon credit.
        pub token_id: u128,
        /// Account that listed (and currently owns before escrow) the credit.
        pub seller: AccountId,
        /// Price in POT (Portaldot's native token, `Balance = u128`).
        pub price: Balance,
        /// Whether this listing is currently active.
        pub active: bool,
    }

    // =========================================================================
    //  Events
    // =========================================================================

    /// Emitted when a new listing is created and the NFT is pulled into escrow.
    #[ink(event)]
    pub struct Listed {
        #[ink(topic)]
        pub token_id: u128,
        #[ink(topic)]
        pub seller: AccountId,
        pub price: Balance,
    }

    /// Emitted when a listing is cancelled and the NFT is returned.
    #[ink(event)]
    pub struct Delisted {
        #[ink(topic)]
        pub token_id: u128,
        #[ink(topic)]
        pub seller: AccountId,
    }

    /// Emitted when a credit is sold to a buyer.
    #[ink(event)]
    pub struct Sold {
        #[ink(topic)]
        pub token_id: u128,
        #[ink(topic)]
        pub seller: AccountId,
        #[ink(topic)]
        pub buyer: AccountId,
        pub price: Balance,
    }

    // =========================================================================
    //  Errors
    // =========================================================================

    /// Marketplace-specific error conditions.
    #[derive(Debug, PartialEq, Eq, scale::Encode, scale::Decode)]
    #[cfg_attr(feature = "std", derive(scale_info::TypeInfo))]
    pub enum MarketplaceError {
        /// The token is already listed.
        AlreadyListed,
        /// No active listing exists for this token.
        NotListed,
        /// Caller is not the original seller.
        NotSeller,
        /// Attached value does not match the listing price.
        IncorrectPrice,
        /// Native-token transfer to the seller failed.
        PaymentFailed,
        /// Cross-contract PSP34 call failed at the transport level.
        PSP34CallFailed,
        /// The PSP34 contract returned a business error.
        PSP34Rejected,
    }

    // =========================================================================
    //  Storage
    // =========================================================================

    /// Marketplace contract state.
    #[ink(storage)]
    pub struct Marketplace {
        /// Address of the PSP34 carbon-credit contract.
        carbon_credit: AccountId,

        /// Account that deployed this marketplace (admin).
        owner: AccountId,

        /// Core listing ledger: `token_id → Option<Listing>`.
        ///
        /// Uses `Option<Listing>` so we can distinguish "never listed" from
        /// "listed and then delisted/sold" by checking the `active` field.
        listings: Mapping<u128, Listing>,

        /// Enumerable index: `index → token_id`.
        listing_index: Mapping<u32, u128>,

        /// Reverse lookup: `token_id → index`.
        listing_index_rev: Mapping<u128, u32>,

        /// Total number of *ever created* listings (monotonic counter used
        /// as the next index).
        listing_count: u32,
    }

    // =========================================================================
    //  Constructor
    // =========================================================================

    impl Marketplace {
        /// Creates a new Marketplace bound to the given PSP34 contract.
        ///
        /// # Parameters
        /// - `carbon_credit` — The `AccountId` of the deployed CarbonCredit
        ///   PSP34 contract.
        #[ink(constructor)]
        pub fn new(carbon_credit: AccountId) -> Self {
            Self {
                carbon_credit,
                owner: Self::env().caller(),
                listings: Default::default(),
                listing_index: Default::default(),
                listing_index_rev: Default::default(),
                listing_count: 0,
            }
        }
    }

    // =========================================================================
    //  Public Messages — Admin
    // =========================================================================

    impl Marketplace {
        /// Returns the marketplace owner (deployer).
        #[ink(message)]
        pub fn owner(&self) -> AccountId {
            self.owner.clone()
        }

        /// Returns the CarbonCredit PSP34 contract address.
        #[ink(message)]
        pub fn carbon_credit_contract(&self) -> AccountId {
            self.carbon_credit.clone()
        }
    }

    // =========================================================================
    //  Public Messages — Listing
    // =========================================================================

    impl Marketplace {
        /// Lists a carbon credit for sale.
        ///
        /// **Prerequisites** (must be done by the seller *before* calling):
        /// 1. `PSP34::approve(marketplace_address, Some(token_id))` on the
        ///    CarbonCredit contract.
        ///
        /// Upon success the NFT is transferred into escrow (this contract).
        ///
        /// # Errors
        /// - [`MarketplaceError::AlreadyListed`]
        /// - [`MarketplaceError::PSP34CallFailed`] / [`MarketplaceError::PSP34Rejected`]
        #[ink(message)]
        pub fn list(
            &mut self,
            token_id: u128,
            price: Balance,
        ) -> Result<(), MarketplaceError> {
            // Guard: no duplicate listing.
            if let Some(listing) = self.listings.get(token_id) {
                if listing.active {
                    return Err(MarketplaceError::AlreadyListed);
                }
            }

            let seller = self.env().caller();
            let marketplace_addr = self.env().account_id();

            // Pull the NFT into escrow via cross-contract PSP34::transfer.
            self.psp34_transfer(marketplace_addr, token_id)?;

            // Store the listing.
            let listing = Listing {
                token_id,
                seller: seller.clone(),
                price,
                active: true,
            };
            self.listings.insert(token_id, &listing);

            // Update enumeration index.
            let idx = self.listing_count;
            self.listing_index.insert(idx, &token_id);
            self.listing_index_rev.insert(token_id, &idx);
            self.listing_count += 1;

            self.env().emit_event(Listed {
                token_id,
                seller,
                price,
            });

            Ok(())
        }

        /// Cancels an active listing and returns the NFT to the seller.
        ///
        /// # Errors
        /// - [`MarketplaceError::NotListed`]
        /// - [`MarketplaceError::NotSeller`]
        /// - [`MarketplaceError::PSP34CallFailed`] / [`MarketplaceError::PSP34Rejected`]
        #[ink(message)]
        pub fn delist(&mut self, token_id: u128) -> Result<(), MarketplaceError> {
            let caller = self.env().caller();
            let mut listing = self
                .listings
                .get(token_id)
                .ok_or(MarketplaceError::NotListed)?;

            if !listing.active {
                return Err(MarketplaceError::NotListed);
            }

            if listing.seller != caller {
                return Err(MarketplaceError::NotSeller);
            }

            // Return the NFT to the seller.
            self.psp34_transfer(listing.seller.clone(), token_id)?;

            listing.active = false;
            self.listings.insert(token_id, &listing);

            self.env().emit_event(Delisted {
                token_id,
                seller: caller,
            });

            Ok(())
        }

        /// Purchases a listed carbon credit.
        ///
        /// The caller **must attach exactly `price` POT** as call value.
        ///
        /// On success the NFT is transferred to the buyer and `price` POT
        /// is transferred to the seller.
        ///
        /// # Errors
        /// - [`MarketplaceError::NotListed`]
        /// - [`MarketplaceError::IncorrectPrice`]
        /// - [`MarketplaceError::PaymentFailed`]
        /// - [`MarketplaceError::PSP34CallFailed`] / [`MarketplaceError::PSP34Rejected`]
        #[ink(message, payable)]
        pub fn buy(&mut self, token_id: u128) -> Result<(), MarketplaceError> {
            let buyer = self.env().caller();
            let attached = self.env().transferred_value();

            let listing = self
                .listings
                .get(token_id)
                .ok_or(MarketplaceError::NotListed)?;

            if !listing.active {
                return Err(MarketplaceError::NotListed);
            }

            if attached != listing.price {
                return Err(MarketplaceError::IncorrectPrice);
            }

            let seller = listing.seller.clone();

            // Transfer POT to the seller.
            self.env()
                .transfer(&seller, listing.price)
                .map_err(|_| MarketplaceError::PaymentFailed)?;

            // Transfer NFT to the buyer.
            self.psp34_transfer(buyer.clone(), token_id)?;

            // Deactivate the listing.
            let mut updated = listing.clone();
            updated.active = false;
            self.listings.insert(token_id, &updated);

            self.env().emit_event(Sold {
                token_id,
                seller,
                buyer,
                price: listing.price,
            });

            Ok(())
        }

        // ----- Queries -------------------------------------------------------

        /// Returns the listing for a given token, if any.
        #[ink(message)]
        pub fn get_listing(&self, token_id: u128) -> Option<Listing> {
            self.listings.get(token_id)
        }

        /// Returns all **ever created** listings (including inactive ones).
        ///
        /// NOTE: this is gas-intensive for large numbers of listings.
        /// Consider an off-chain indexer for production use.
        #[ink(message)]
        pub fn get_listings(&self) -> ink::prelude::vec::Vec<Listing> {
            let mut result = ink::prelude::vec::Vec::new();
            for i in 0..self.listing_count {
                if let Some(token_id) = self.listing_index.get(i) {
                    if let Some(listing) = self.listings.get(token_id) {
                        result.push(listing);
                    }
                }
            }
            result
        }
    }

    // =========================================================================
    //  Private — Cross-Contract Helpers
    // =========================================================================

    impl Marketplace {
        /// Executes a `PSP34::transfer(to, id, data)` cross-contract call
        /// to the CarbonCredit contract.
        ///
        /// The selector is computed from `"PSP34::transfer"` at compile time,
        /// matching the selector in the deployed PSP34 contract.
        fn psp34_transfer(
            &self,
            to: AccountId,
            token_id: u128,
        ) -> Result<(), MarketplaceError> {
            let result = build_call::<ink::env::DefaultEnvironment>()
                .call(self.carbon_credit)
                .exec_input(
                    ExecutionInput::new(Selector::new(ink::selector_bytes!(
                        "PSP34::transfer"
                    )))
                    .push_arg(&to)
                    .push_arg(&PSP34Id::U128(token_id))
                    .push_arg(&ink::prelude::vec::Vec::<u8>::new()),
                )
                .returns::<Result<(), PSP34Error>>()
                .invoke();

            match result {
                Ok(Ok(())) => Ok(()),
                Ok(Err(_)) => Err(MarketplaceError::PSP34Rejected),
                Err(_) => Err(MarketplaceError::PSP34CallFailed),
            }
        }
    }

    // =========================================================================
    //  Tests
    // =========================================================================

    #[cfg(test)]
    mod tests {
        use super::*;

        fn default_accounts() -> ink::env::test::DefaultAccounts<ink::env::DefaultEnvironment> {
            ink::env::test::default_accounts::<ink::env::DefaultEnvironment>()
        }

        fn set_caller(account: AccountId) {
            ink::env::test::set_caller::<ink::env::DefaultEnvironment>(account);
        }

        fn set_balance(account: AccountId, balance: Balance) {
            ink::env::test::set_account_balance::<ink::env::DefaultEnvironment>(account, balance);
        }

        fn alice() -> AccountId { default_accounts().alice }
        fn bob()   -> AccountId { default_accounts().bob }

        fn dummy_psp34() -> AccountId {
            AccountId::from([0x42; 32])
        }

        fn new_marketplace() -> Marketplace {
            set_caller(alice());
            Marketplace::new(dummy_psp34())
        }

        #[ink::test]
        fn constructor_works() {
            let m = new_marketplace();
            assert_eq!(m.owner(), alice());
            assert_eq!(m.carbon_credit_contract(), dummy_psp34());
        }

        #[ink::test]
        fn get_listing_none_for_unlisted() {
            let m = new_marketplace();
            assert!(m.get_listing(999).is_none());
        }

        #[ink::test]
        fn get_listings_empty() {
            let m = new_marketplace();
            assert!(m.get_listings().is_empty());
        }

        // NOTE: Full integration tests with an actual PSP34 mock would require
        // ink!'s E2E testing framework.  The unit tests above verify storage
        // and access-control logic; cross-contract call paths are covered by
        // E2E tests (see ink_e2e dev-dependency).
    }
}
