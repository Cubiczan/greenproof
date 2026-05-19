//! # GreenVerify AI — Carbon Credit NFT
//!
//! An **PSP34** (ink!'s ERC-721 equivalent) non-fungible token where each
//! minted token represents **one tonne of verified CO₂ offset**.
//!
//! ## Architecture
//!
//! This contract is built on top of [OpenBrush]'s PSP34 implementation with
//! the `Enumerable` extension, giving us `total_supply()` and per-owner
//! balance queries out of the box.
//!
//! Every token carries a rich [`CreditData`] payload that captures the
//! project metadata required for carbon-credit compliance (verification
//! standard, vintage year, project type, country, verifier identity, …).
//!
//! ## Key Concepts
//!
//! | Concept            | Details                                             |
//! |--------------------|-----------------------------------------------------|
//! | Token ID scheme    | Incremental `u128` wrapped in `Id::U128`            |
//! | Ownership model    | Single owner (deployer) may mint; any holder burns |
//! | Burn semantics     | "Retirement" — permanently removes the offset       |
//!
//! ## Transactions
//!
//! 1. **Minting** — Only the contract owner can mint credits.  The owner
//!    supplies the recipient and a [`CreditData`] struct.
//! 2. **Transfer** — Standard PSP34 transfer; the built-in `Transfer`
//!    event is supplemented by a `CreditTransferred` wrapper.
//! 3. **Retirement (burn)** — Any token holder may burn (retire) their
//!    credit.  The metadata is purged on-chain.
//!
//! [OpenBrush]: https://github.com/Brushfam/openbrush-contracts

#![cfg_attr(not(feature = "std"), no_std)]

/// Re-export ink's prelude so downstream code can use `String`, `Vec`, etc.
#[ink::contract]
pub mod carbon_credit {

    // =========================================================================
    //  Imports
    // =========================================================================

    /// Brings in the PSP34 base traits, error types, `Id` enum, and internal
    /// helpers (`_mint_to`, `_burn_from`, …).
    use openbrush::contracts::psp34::extensions::enumerable::*;

    // =========================================================================
    //  Custom Types
    // =========================================================================

    /// Recognised carbon-credit verification standards.
    ///
    /// | Variant       | Full Name                        |
    /// |---------------|----------------------------------|
    /// | `VCS`         | Verified Carbon Standard         |
    /// | `GS`          | Gold Standard (legacy label)     |
    /// | `CDM`         | Clean Development Mechanism      |
    /// | `GoldStandard`| Gold Standard for the Global Goals|
    #[derive(
        scale::Encode, scale::Decode, Clone, Debug, PartialEq, Eq, Copy,
    )]
    #[cfg_attr(
        feature = "std",
        derive(scale_info::TypeInfo, ink::storage::traits::StorageLayout)
    )]
    pub enum CreditStandard {
        VCS,
        GS,
        CDM,
        GoldStandard,
    }

    /// Categories of carbon-mitigation projects.
    #[derive(
        scale::Encode, scale::Decode, Clone, Debug, PartialEq, Eq, Copy,
    )]
    #[cfg_attr(
        feature = "std",
        derive(scale_info::TypeInfo, ink::storage::traits::StorageLayout)
    )]
    pub enum ProjectType {
        Reforestation,
        Renewable,
        MethaneCapture,
    }

    /// Full metadata attached to every carbon-credit token.
    ///
    /// This struct is stored **on-chain** in a `Mapping<Id, CreditData>` and
    /// can be retrieved via [`CarbonCredit::get_credit_info`].
    #[derive(
        scale::Encode, scale::Decode, Clone, Debug, PartialEq, Eq,
    )]
    #[cfg_attr(
        feature = "std",
        derive(scale_info::TypeInfo, ink::storage::traits::StorageLayout)
    )]
    pub struct CreditData {
        /// Human-readable project name (e.g. "Amazon Reforestation Phase II").
        pub project_name: ink::prelude::string::String,
        /// Unix timestamp of the most recent verification.
        pub verification_date: u64,
        /// Account that performed the AI / manual verification.
        pub verifier: AccountId,
        /// Year the carbon offset was generated.
        pub vintage_year: u32,
        /// Verification standard under which the credit was issued.
        pub credit_standard: CreditStandard,
        /// ISO 3166-1 alpha-2 country code (e.g. "BR").
        pub country: ink::prelude::string::String,
        /// Category of the mitigation project.
        pub project_type: ProjectType,
    }

    // =========================================================================
    //  Events
    // =========================================================================

    /// Emitted when a new carbon credit is minted.
    #[ink(event)]
    pub struct CreditMinted {
        /// The newly created token ID (`u128`).
        #[ink(topic)]
        pub token_id: u128,
        /// Account that received the token.
        #[ink(topic)]
        pub to: AccountId,
        /// Project name for easy indexing.
        pub project_name: ink::prelude::string::String,
    }

    /// Emitted when a carbon credit is transferred between accounts.
    #[ink(event)]
    pub struct CreditTransferred {
        /// Previous holder (`None` for mints).
        #[ink(topic)]
        pub from: Option<AccountId>,
        /// New holder (`None` for burns).
        #[ink(topic)]
        pub to: Option<AccountId>,
        /// The token that moved.
        pub token_id: u128,
    }

    /// Emitted when a carbon credit is burned (retired).
    #[ink(event)]
    pub struct CreditRetired {
        /// The token that was permanently removed.
        #[ink(topic)]
        pub token_id: u128,
        /// Account that retired the credit.
        #[ink(topic)]
        pub owner: AccountId,
    }

    // =========================================================================
    //  Errors
    // =========================================================================

    /// Errors specific to the carbon-credit contract on top of PSP34 errors.
    #[derive(Debug, PartialEq, Eq, scale::Encode, scale::Decode)]
    #[cfg_attr(feature = "std", derive(scale_info::TypeInfo))]
    pub enum CarbonCreditError {
        /// Returned when a non-owner attempts to mint.
        CallerNotOwner,
        /// Returned when the requested token ID does not exist.
        TokenNotFound,
    }

    // =========================================================================
    //  Storage
    // =========================================================================

    /// The main contract storage.
    ///
    /// Contains the OpenBrush PSP34 + Enumerable fields (marked with
    /// `#[storage_field]`) plus our custom mappings.
    #[derive(Default, openbrush::Storage)]
    #[ink(storage)]
    pub struct CarbonCredit {
        /// OpenBrush PSP34 base data (owner_of ledger, balances, approvals).
        #[storage_field]
        psp34: psp34::Data,

        /// OpenBrush Enumerable extension data (token enumeration).
        #[storage_field]
        enumerable: enumerable::Data,

        /// Account that deployed the contract — the only address allowed to
        /// mint new credits.
        owner: AccountId,

        /// Monotonic counter used to generate the next `u128` token ID.
        next_token_id: u128,

        /// Maps `Id::U128(n)` → [`CreditData`] for every minted credit.
        credit_info: Mapping<Id, CreditData>,

        /// Maps `blake2b256(project_name)` → `Vec<u128>` for efficient
        /// "all credits in project X" queries.
        credits_by_project: Mapping<[u8; 32], ink::prelude::vec::Vec<u128>>,
    }

    // =========================================================================
    //  PSP34 Trait Implementations (OpenBrush default bodies)
    // =========================================================================

    /// Delegate to the OpenBrush default PSP34 implementation.
    impl PSP34 for CarbonCredit {}

    /// Delegate to the OpenBrush default PSP34Enumerable implementation.
    impl PSP34Enumerable for CarbonCredit {}

    /// OpenBrush internal helpers — `self._mint_to()`, `self._burn_from()`, etc.
    impl psp34::Internal for CarbonCredit {}

    /// Enumerable internal helpers.
    impl enumerable::Internal for CarbonCredit {}

    // =========================================================================
    //  Constructor
    // =========================================================================

    impl CarbonCredit {
        /// Creates a new CarbonCredit contract.
        ///
        /// The caller becomes the **owner** and is the only account that may
        /// mint new credits.
        #[ink(constructor)]
        pub fn new() -> Self {
            Self {
                psp34: Default::default(),
                enumerable: Default::default(),
                owner: Self::env().caller(),
                next_token_id: 1, // start at 1 so 0 is never a valid ID
                credit_info: Default::default(),
                credits_by_project: Default::default(),
            }
        }
    }

    // =========================================================================
    //  Public Messages
    // =========================================================================

    impl CarbonCredit {
        // ----- Ownership -----------------------------------------------------

        /// Returns the account that deployed (owns) this contract.
        #[ink(message)]
        pub fn owner(&self) -> AccountId {
            self.owner.clone()
        }

        /// Transfers contract ownership to `new_owner`.
        ///
        /// # Panics
        /// Reverts if the caller is not the current owner.
        #[ink(message)]
        pub fn transfer_ownership(&mut self, new_owner: AccountId) {
            self.ensure_owner();
            self.owner = new_owner;
        }

        // ----- Mint ----------------------------------------------------------

        /// Mints a new carbon credit and assigns it to `to`.
        ///
        /// Only the contract **owner** may call this.  Each call creates one
        /// token representing 1 tonne of verified CO₂ offset.
        ///
        /// # Parameters
        /// - `to` — Recipient account.
        /// - `metadata` — Full [`CreditData`] payload.
        ///
        /// # Errors
        /// Returns [`PSP34Error::TokenExists`] if the internal token ID
        /// counter somehow collides (practically impossible with `u128`).
        #[ink(message)]
        pub fn mint(
            &mut self,
            to: AccountId,
            metadata: CreditData,
        ) -> Result<(), PSP34Error> {
            self.ensure_owner();

            let token_id_u128 = self.next_token_id;
            self.next_token_id += 1;
            let id = Id::U128(token_id_u128);

            // Persist the rich metadata.
            self.credit_info.insert(&id, &metadata);

            // Append to the project-indexed list.
            let project_key = Self::project_name_hash(&metadata.project_name);
            let mut tokens = self
                .credits_by_project
                .get(&project_key)
                .unwrap_or_default();
            tokens.push(token_id_u128);
            self.credits_by_project.insert(&project_key, &tokens);

            // Delegate the actual NFT mint to OpenBrush.
            self._mint_to(&to, &id)?;

            // Emit our domain-specific event.
            self.env().emit_event(CreditMinted {
                token_id: token_id_u128,
                to: to.clone(),
                project_name: metadata.project_name.clone(),
            });

            Ok(())
        }

        // ----- Burn (Retire) -------------------------------------------------

        /// Burns (retires) a carbon credit permanently.
        ///
        /// The caller **must be the token owner**.  On-chain metadata is
        /// removed after the burn.
        ///
        /// # Parameters
        /// - `token_id` — The `u128` part of the PSP34 `Id::U128`.
        ///
        /// # Errors
        /// - [`PSP34Error::TokenNotExists`] if the token does not exist.
        /// - [`PSP34Error::NotApproved`] if the caller is not the owner.
        #[ink(message)]
        pub fn burn(&mut self, token_id: u128) -> Result<(), PSP34Error> {
            let caller = Self::env().caller();
            let id = Id::U128(token_id);

            // Delegate the actual NFT burn to OpenBrush.
            self._burn_from(&caller, &id)?;

            // Remove the metadata (gas refund).
            self.credit_info.remove(&id);

            // Emit the retirement event.
            self.env().emit_event(CreditRetired {
                token_id,
                owner: caller,
            });

            Ok(())
        }

        // ----- Transfer wrapper ----------------------------------------------

        /// Transfers a carbon credit to another account.
        ///
        /// This is a convenience wrapper around the standard PSP34
        /// `transfer` that additionally emits the [`CreditTransferred`]
        /// event for downstream tooling.
        #[ink(message)]
        pub fn transfer_credit(
            &mut self,
            to: AccountId,
            token_id: u128,
        ) -> Result<(), PSP34Error> {
            let caller = Self::env().caller();
            let id = Id::U128(token_id);

            // Call the OpenBrush default PSP34 transfer.
            PSP34::transfer(self, to.clone(), id.clone(), ink::prelude::vec::Vec::new())?;

            self.env().emit_event(CreditTransferred {
                from: Some(caller),
                to: Some(to),
                token_id,
            });

            Ok(())
        }

        // ----- Queries -------------------------------------------------------

        /// Returns the [`CreditData`] attached to a given token.
        ///
        /// # Errors
        /// Returns [`CarbonCreditError::TokenNotFound`] if no credit has been
        /// minted with the supplied ID.
        #[ink(message)]
        pub fn get_credit_info(
            &self,
            token_id: u128,
        ) -> Result<CreditData, CarbonCreditError> {
            let id = Id::U128(token_id);
            self.credit_info
                .get(&id)
                .ok_or(CarbonCreditError::TokenNotFound)
        }

        /// Returns **all** `u128` token IDs minted under the given project.
        ///
        /// The `project_name` is hashed with Blake2x256 to produce the
        /// storage lookup key.
        ///
        /// Returns an empty `Vec` if no credits exist for the project.
        #[ink(message)]
        pub fn credits_by_project(
            &self,
            project_name: ink::prelude::string::String,
        ) -> ink::prelude::vec::Vec<u128> {
            let key = Self::project_name_hash(&project_name);
            self.credits_by_project.get(&key).unwrap_or_default()
        }
    }

    // =========================================================================
    //  Private Helpers
    // =========================================================================

    impl CarbonCredit {
        /// Asserts that the caller is the contract owner; reverts otherwise.
        fn ensure_owner(&self) {
            assert_eq!(
                Self::env().caller(),
                self.owner,
                "CarbonCredit: caller is not the owner"
            );
        }

        /// Computes `Blake2x256(project_name)` → `[u8; 32]` used as the
        /// mapping key for the `credits_by_project` index.
        fn project_name_hash(name: &str) -> [u8; 32] {
            use ink::env::hash::Blake2x256;
            ink::env::hash_bytes::<Blake2x256>(name.as_bytes())
        }
    }

    // =========================================================================
    //  Tests (off-chain, `#[cfg(test)]`)
    // =========================================================================

    #[cfg(test)]
    mod tests {
        use super::*;

        // Helper to set up a default account as the "owner".
        fn default_accounts() -> ink::env::test::DefaultAccounts<ink::env::DefaultEnvironment> {
            ink::env::test::default_accounts::<ink::env::DefaultEnvironment>()
        }

        fn set_caller(account: AccountId) {
            ink::env::test::set_caller::<ink::env::DefaultEnvironment>(account);
        }

        fn alice() -> AccountId {
            default_accounts().alice
        }

        fn bob() -> AccountId {
            default_accounts().bob
        }

        /// Utility: construct a minimal [`CreditData`] for testing.
        fn sample_credit(project: &str) -> CreditData {
            CreditData {
                project_name: project.to_owned(),
                verification_date: 1_700_000_000,
                verifier: bob(),
                vintage_year: 2024,
                credit_standard: CreditStandard::VCS,
                country: "BR".to_owned(),
                project_type: ProjectType::Reforestation,
            }
        }

        #[ink::test]
        fn constructor_sets_owner() {
            let contract = CarbonCredit::new();
            assert_eq!(contract.owner(), alice());
        }

        #[ink::test]
        fn mint_works() {
            set_caller(alice());
            let mut contract = CarbonCredit::new();
            let credit = sample_credit("Alpha Forest");
            assert!(contract.mint(bob(), credit.clone()).is_ok());
            assert_eq!(contract.total_supply(), 1);
        }

        #[ink::test]
        fn mint_emits_event() {
            set_caller(alice());
            let mut contract = CarbonCredit::new();
            let credit = sample_credit("Alpha Forest");
            let _ = contract.mint(bob(), credit);

            let emitted = contract.env().emit_returned_events::<CreditMinted>();
            assert_eq!(emitted.len(), 1);
            assert_eq!(emitted[0].to, bob());
        }

        #[ink::test]
        #[should_panic(expected = "caller is not the owner")]
        fn mint_fails_for_non_owner() {
            set_caller(alice());
            let mut contract = CarbonCredit::new();
            set_caller(bob());
            let _ = contract.mint(bob(), sample_credit("Bad"));
        }

        #[ink::test]
        fn burn_reduces_supply() {
            set_caller(alice());
            let mut contract = CarbonCredit::new();
            let credit = sample_credit("Beta Wind");
            let _ = contract.mint(bob(), credit);
            assert_eq!(contract.total_supply(), 1);

            set_caller(bob());
            let _ = contract.burn(1);
            assert_eq!(contract.total_supply(), 0);
        }

        #[ink::test]
        fn get_credit_info_roundtrip() {
            set_caller(alice());
            let mut contract = CarbonCredit::new();
            let credit = sample_credit("Gamma Solar");
            let _ = contract.mint(bob(), credit.clone());
            let fetched = contract.get_credit_info(1).unwrap();
            assert_eq!(fetched.project_name, "Gamma Solar");
            assert_eq!(fetched.vintage_year, 2024);
        }

        #[ink::test]
        fn credits_by_project_returns_correct_ids() {
            set_caller(alice());
            let mut contract = CarbonCredit::new();
            let _ = contract.mint(bob(), sample_credit("Delta Methane"));
            let _ = contract.mint(bob(), sample_credit("Delta Methane"));
            let _ = contract.mint(bob(), sample_credit("Other Project"));

            let ids = contract.credits_by_project("Delta Methane".to_owned());
            assert_eq!(ids.len(), 2);
            assert!(ids.contains(&1));
            assert!(ids.contains(&2));
        }

        #[ink::test]
        fn credits_by_project_empty_for_unknown() {
            let contract = CarbonCredit::new();
            let ids = contract.credits_by_project("Nonexistent".to_owned());
            assert!(ids.is_empty());
        }
    }
}
