//! # GreenVerify AI — Carbon Credit NFT
//!
//! A **PSP34** (ink!'s ERC-721 equivalent) non-fungible token where each
//! minted token represents **one tonne of verified CO₂ offset**.
//!
//! ## Architecture
//!
//! This contract implements the PSP34 NFT primitives **natively** on top of
//! [`ink::storage::Mapping`] — ownership ledger, balances, token + operator
//! approvals, total supply, and a full enumerable index (global and
//! per-owner). It requires **no external framework** and builds on **stable
//! Rust with ink! 5** (no nightly `#![feature(...)]`).
//!
//! It was previously built on OpenBrush's PSP34 + Enumerable implementation,
//! which pulled in `#![feature(min_specialization)]` (nightly) and only
//! supported ink! 4. The public surface — token ID scheme, error variants,
//! and event shapes — is kept binary-compatible with the PSP34 spec so the
//! `marketplace` contract's cross-contract calls keep working unchanged.
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

#![cfg_attr(not(feature = "std"), no_std)]

/// The carbon credit NFT contract.
#[ink::contract]
pub mod carbon_credit {

    // =========================================================================
    //  Imports
    // =========================================================================

    use ink::prelude::vec::Vec;
    use ink::storage::Mapping;

    // =========================================================================
    //  PSP34 spec-compatible types
    // =========================================================================

    /// PSP34 Token ID.
    ///
    /// Variant ordering and field types mirror the PSP34 specification exactly
    /// so SCALE encoding/decoding is binary-compatible with the `marketplace`
    /// contract's cross-contract calls.
    #[derive(scale::Encode, scale::Decode, Clone, Debug, PartialEq, Eq)]
    #[cfg_attr(
        feature = "std",
        derive(scale_info::TypeInfo, ink::storage::traits::StorageLayout)
    )]
    pub enum Id {
        U8(u8),
        U16(u16),
        U32(u32),
        U64(u64),
        U128(u128),
        Bytes(Vec<u8>),
    }

    /// PSP34 Error — mirrors the spec so cross-contract callers can SCALE-decode
    /// the return value of `transfer` / `approve` calls.
    #[derive(scale::Encode, scale::Decode, Clone, Debug, PartialEq, Eq)]
    #[cfg_attr(
        feature = "std",
        derive(scale_info::TypeInfo, ink::storage::traits::StorageLayout)
    )]
    pub enum PSP34Error {
        /// Custom error with a free-form message (PSP34 spec variant 0).
        Custom(Vec<u8>),
        /// The token does not exist.
        TokenNotExists,
        /// The token already exists.
        TokenExists,
        /// The caller is not the owner nor an approved operator.
        NotApproved,
        /// Cannot approve oneself / self transfer not allowed.
        SelfApprove,
        /// A safe-transfer recipient check failed.
        SafeTransferCheckFailed(Vec<u8>),
    }

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
    #[derive(scale::Encode, scale::Decode, Clone, Debug, PartialEq, Eq, Copy)]
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
    #[derive(scale::Encode, scale::Decode, Clone, Debug, PartialEq, Eq, Copy)]
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
    #[derive(scale::Encode, scale::Decode, Clone, Debug, PartialEq, Eq)]
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

    /// PSP34 standard `Transfer` event — emitted on mint, transfer and burn.
    #[ink(event)]
    pub struct Transfer {
        /// Previous holder (`None` for mints).
        #[ink(topic)]
        pub from: Option<AccountId>,
        /// New holder (`None` for burns).
        #[ink(topic)]
        pub to: Option<AccountId>,
        /// The token that moved.
        #[ink(topic)]
        pub id: Id,
    }

    /// PSP34 standard `Approval` event.
    #[ink(event)]
    pub struct Approval {
        /// Token owner granting the approval.
        #[ink(topic)]
        pub owner: AccountId,
        /// The approved operator.
        #[ink(topic)]
        pub operator: AccountId,
        /// The specific token approved (`None` = approval for all tokens).
        #[ink(topic)]
        pub id: Option<Id>,
        /// Whether the approval is granted (`true`) or revoked (`false`).
        pub approved: bool,
    }

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
    /// Implements the PSP34 ownership / balance / approval ledgers and a full
    /// enumerable index natively, plus the carbon-credit domain fields.
    #[ink(storage)]
    pub struct CarbonCredit {
        // ----- PSP34 core ledgers -------------------------------------------
        /// `token_id -> owner` ownership ledger.
        token_owner: Mapping<Id, AccountId>,
        /// `owner -> number of tokens held`.
        owned_tokens_count: Mapping<AccountId, u32>,
        /// Per-token approval: `token_id -> approved operator`.
        token_approvals: Mapping<Id, AccountId>,
        /// Operator-for-all approval: `(owner, operator) -> ()`.
        operator_approvals: Mapping<(AccountId, AccountId), ()>,

        // ----- Enumerable index ---------------------------------------------
        /// Total number of tokens currently in existence.
        total_supply: u128,
        /// Global enumeration: `index -> token_id`.
        tokens_index: Mapping<u128, Id>,
        /// Reverse global enumeration: `token_id -> index` (for O(1) removal).
        tokens_index_of: Mapping<Id, u128>,
        /// Per-owner enumeration: `(owner, index) -> token_id`.
        owned_tokens: Mapping<(AccountId, u32), Id>,
        /// Reverse per-owner enumeration: `token_id -> index in owner's list`.
        owned_tokens_index: Mapping<Id, u32>,

        // ----- Carbon-credit domain -----------------------------------------
        /// Account that deployed the contract — the only address allowed to
        /// mint new credits.
        owner: AccountId,
        /// Monotonic counter used to generate the next `u128` token ID.
        next_token_id: u128,
        /// Maps `Id::U128(n)` → [`CreditData`] for every minted credit.
        credit_info: Mapping<Id, CreditData>,
        /// Maps `blake2b256(project_name)` → `Vec<u128>` for efficient
        /// "all credits in project X" queries.
        credits_by_project: Mapping<[u8; 32], Vec<u128>>,
    }

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
                token_owner: Mapping::default(),
                owned_tokens_count: Mapping::default(),
                token_approvals: Mapping::default(),
                operator_approvals: Mapping::default(),
                total_supply: 0,
                tokens_index: Mapping::default(),
                tokens_index_of: Mapping::default(),
                owned_tokens: Mapping::default(),
                owned_tokens_index: Mapping::default(),
                owner: Self::env().caller(),
                next_token_id: 1, // start at 1 so 0 is never a valid ID
                credit_info: Mapping::default(),
                credits_by_project: Mapping::default(),
            }
        }
    }

    impl Default for CarbonCredit {
        fn default() -> Self {
            Self::new()
        }
    }

    // =========================================================================
    //  PSP34 standard messages (native implementation)
    // =========================================================================

    impl CarbonCredit {
        /// Returns the number of tokens held by `owner`.
        #[ink(message)]
        pub fn balance_of(&self, owner: AccountId) -> u32 {
            self.owned_tokens_count.get(owner).unwrap_or(0)
        }

        /// Returns the owner of token `id`, or `None` if it does not exist.
        #[ink(message)]
        pub fn owner_of(&self, id: Id) -> Option<AccountId> {
            self.token_owner.get(&id)
        }

        /// Returns whether `operator` is approved to manage `id` (or all of
        /// `owner`'s tokens when `id` is `None`).
        #[ink(message)]
        pub fn allowance(
            &self,
            owner: AccountId,
            operator: AccountId,
            id: Option<Id>,
        ) -> bool {
            self.is_approved(owner, operator, id.as_ref())
        }

        /// Approves (or revokes) `operator` for a single token (`id = Some`) or
        /// for all of the caller's tokens (`id = None`).
        #[ink(message)]
        pub fn approve(
            &mut self,
            operator: AccountId,
            id: Option<Id>,
            approved: bool,
        ) -> Result<(), PSP34Error> {
            let caller = self.env().caller();
            if caller == operator {
                return Err(PSP34Error::SelfApprove);
            }

            match id.clone() {
                Some(token_id) => {
                    // Per-token approval — caller must own (or be operator of)
                    // the token.
                    let token_owner = self
                        .token_owner
                        .get(&token_id)
                        .ok_or(PSP34Error::TokenNotExists)?;
                    if token_owner != caller
                        && !self.operator_approvals.contains((token_owner, caller))
                    {
                        return Err(PSP34Error::NotApproved);
                    }
                    if approved {
                        self.token_approvals.insert(&token_id, &operator);
                    } else {
                        self.token_approvals.remove(&token_id);
                    }
                }
                None => {
                    // Operator-for-all approval.
                    if approved {
                        self.operator_approvals.insert((caller, operator), &());
                    } else {
                        self.operator_approvals.remove((caller, operator));
                    }
                }
            }

            self.env().emit_event(Approval {
                owner: caller,
                operator,
                id,
                approved,
            });
            Ok(())
        }

        /// Standard PSP34 transfer of token `id` to `to`.
        ///
        /// The caller must be the owner or an approved operator.
        #[ink(message)]
        pub fn transfer(
            &mut self,
            to: AccountId,
            id: Id,
            _data: Vec<u8>,
        ) -> Result<(), PSP34Error> {
            let caller = self.env().caller();
            self.transfer_token(caller, to, id)
        }

        /// Returns the total number of tokens in existence.
        #[ink(message)]
        pub fn total_supply(&self) -> u128 {
            self.total_supply
        }

        /// Enumerable: returns the token at the global `index`.
        #[ink(message)]
        pub fn token_by_index(&self, index: u128) -> Option<Id> {
            self.tokens_index.get(index)
        }

        /// Enumerable: returns the `index`-th token owned by `owner`.
        #[ink(message)]
        pub fn owners_token_by_index(
            &self,
            owner: AccountId,
            index: u32,
        ) -> Option<Id> {
            self.owned_tokens.get((owner, index))
        }
    }

    // =========================================================================
    //  Carbon-credit domain messages
    // =========================================================================

    impl CarbonCredit {
        // ----- Ownership -----------------------------------------------------

        /// Returns the account that deployed (owns) this contract.
        #[ink(message)]
        pub fn owner(&self) -> AccountId {
            self.owner
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
        /// Returns [`PSP34Error::TokenExists`] if the internal token ID counter
        /// somehow collides (practically impossible with `u128`).
        #[ink(message)]
        pub fn mint(
            &mut self,
            to: AccountId,
            metadata: CreditData,
        ) -> Result<(), PSP34Error> {
            self.ensure_owner();

            let token_id_u128 = self.next_token_id;
            let id = Id::U128(token_id_u128);

            if self.token_owner.contains(&id) {
                return Err(PSP34Error::TokenExists);
            }
            self.next_token_id += 1;

            // Persist the rich metadata.
            self.credit_info.insert(&id, &metadata);

            // Append to the project-indexed list.
            let project_key = Self::project_name_hash(&metadata.project_name);
            let mut tokens =
                self.credits_by_project.get(project_key).unwrap_or_default();
            tokens.push(token_id_u128);
            self.credits_by_project.insert(project_key, &tokens);

            // Perform the native NFT mint (ledgers + enumerable index).
            self.add_token_to(&to, &id);

            // Emit the standard PSP34 Transfer event (None -> to).
            self.env().emit_event(Transfer {
                from: None,
                to: Some(to),
                id: id.clone(),
            });

            // Emit our domain-specific event.
            self.env().emit_event(CreditMinted {
                token_id: token_id_u128,
                to,
                project_name: metadata.project_name,
            });

            Ok(())
        }

        // ----- Burn (Retire) -------------------------------------------------

        /// Burns (retires) a carbon credit permanently.
        ///
        /// The caller **must be the token owner or an approved operator**.
        /// On-chain metadata is removed after the burn.
        ///
        /// # Parameters
        /// - `token_id` — The `u128` part of the PSP34 `Id::U128`.
        ///
        /// # Errors
        /// - [`PSP34Error::TokenNotExists`] if the token does not exist.
        /// - [`PSP34Error::NotApproved`] if the caller is not the owner / not
        ///   approved.
        #[ink(message)]
        pub fn burn(&mut self, token_id: u128) -> Result<(), PSP34Error> {
            let caller = self.env().caller();
            let id = Id::U128(token_id);

            let token_owner =
                self.token_owner.get(&id).ok_or(PSP34Error::TokenNotExists)?;

            if !self.approved_or_owner(caller, token_owner, &id) {
                return Err(PSP34Error::NotApproved);
            }

            // Perform the native NFT burn (ledgers + enumerable index).
            self.remove_token_from(&token_owner, &id);
            self.token_approvals.remove(&id);

            // Remove the metadata (gas refund).
            self.credit_info.remove(&id);

            // Emit the standard PSP34 Transfer event (owner -> None).
            self.env().emit_event(Transfer {
                from: Some(token_owner),
                to: None,
                id,
            });

            // Emit the retirement event.
            self.env().emit_event(CreditRetired {
                token_id,
                owner: token_owner,
            });

            Ok(())
        }

        // ----- Transfer wrapper ----------------------------------------------

        /// Transfers a carbon credit to another account.
        ///
        /// This is a convenience wrapper around the standard PSP34 `transfer`
        /// that additionally emits the [`CreditTransferred`] event for
        /// downstream tooling.
        #[ink(message)]
        pub fn transfer_credit(
            &mut self,
            to: AccountId,
            token_id: u128,
        ) -> Result<(), PSP34Error> {
            let caller = self.env().caller();
            let id = Id::U128(token_id);

            self.transfer_token(caller, to, id)?;

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
        /// The `project_name` is hashed with Blake2x256 to produce the storage
        /// lookup key.
        ///
        /// Returns an empty `Vec` if no credits exist for the project.
        #[ink(message)]
        pub fn credits_by_project(
            &self,
            project_name: ink::prelude::string::String,
        ) -> Vec<u128> {
            let key = Self::project_name_hash(&project_name);
            self.credits_by_project.get(key).unwrap_or_default()
        }
    }

    // =========================================================================
    //  Private Helpers
    // =========================================================================

    // `#[ink(impl)]` lets these non-message helpers use `Self::env()` /
    // `self.env()` for caller lookup and event emission.
    #[ink(impl)]
    impl CarbonCredit {
        /// Asserts that the caller is the contract owner; reverts otherwise.
        fn ensure_owner(&self) {
            assert_eq!(
                Self::env().caller(),
                self.owner,
                "CarbonCredit: caller is not the owner"
            );
        }

        /// Computes `Blake2x256(project_name)` → `[u8; 32]` used as the mapping
        /// key for the `credits_by_project` index.
        fn project_name_hash(name: &str) -> [u8; 32] {
            use ink::env::hash::Blake2x256;
            let mut output = [0u8; 32];
            ink::env::hash_bytes::<Blake2x256>(name.as_bytes(), &mut output);
            output
        }

        /// Whether `operator` is approved for `id` / for all of `owner`'s
        /// tokens.
        fn is_approved(
            &self,
            owner: AccountId,
            operator: AccountId,
            id: Option<&Id>,
        ) -> bool {
            if self.operator_approvals.contains((owner, operator)) {
                return true;
            }
            if let Some(id) = id {
                if self.token_approvals.get(id) == Some(operator) {
                    return true;
                }
            }
            false
        }

        /// Whether `caller` may move/burn `id` owned by `token_owner`.
        fn approved_or_owner(
            &self,
            caller: AccountId,
            token_owner: AccountId,
            id: &Id,
        ) -> bool {
            caller == token_owner
                || self.is_approved(token_owner, caller, Some(id))
        }

        /// Core transfer routine shared by `transfer` and `transfer_credit`.
        fn transfer_token(
            &mut self,
            caller: AccountId,
            to: AccountId,
            id: Id,
        ) -> Result<(), PSP34Error> {
            let token_owner =
                self.token_owner.get(&id).ok_or(PSP34Error::TokenNotExists)?;

            if !self.approved_or_owner(caller, token_owner, &id) {
                return Err(PSP34Error::NotApproved);
            }

            // Clear any single-token approval on transfer.
            self.token_approvals.remove(&id);

            self.remove_token_from(&token_owner, &id);
            self.add_token_to(&to, &id);

            Self::env().emit_event(Transfer {
                from: Some(token_owner),
                to: Some(to),
                id,
            });

            Ok(())
        }

        /// Adds `id` to `to`'s holdings and the enumerable indices.
        fn add_token_to(&mut self, to: &AccountId, id: &Id) {
            // Ownership ledger.
            self.token_owner.insert(id, to);

            // Per-owner balance + per-owner enumeration.
            let balance = self.owned_tokens_count.get(to).unwrap_or(0);
            self.owned_tokens.insert((*to, balance), id);
            self.owned_tokens_index.insert(id, &balance);
            self.owned_tokens_count.insert(to, &(balance + 1));

            // Global enumeration + total supply.
            let supply = self.total_supply;
            self.tokens_index.insert(supply, id);
            self.tokens_index_of.insert(id, &supply);
            self.total_supply = supply + 1;
        }

        /// Removes `id` from `from`'s holdings and the enumerable indices,
        /// using the standard swap-and-pop to keep indices contiguous.
        fn remove_token_from(&mut self, from: &AccountId, id: &Id) {
            // ---- Per-owner enumeration (swap & pop) ----
            let last_index = self
                .owned_tokens_count
                .get(from)
                .unwrap_or(0)
                .saturating_sub(1);
            let token_index = self.owned_tokens_index.get(id).unwrap_or(0);

            if token_index != last_index {
                if let Some(last_token) =
                    self.owned_tokens.get((*from, last_index))
                {
                    self.owned_tokens.insert((*from, token_index), &last_token);
                    self.owned_tokens_index.insert(&last_token, &token_index);
                }
            }
            self.owned_tokens.remove((*from, last_index));
            self.owned_tokens_index.remove(id);
            self.owned_tokens_count.insert(from, &last_index);

            // ---- Global enumeration (swap & pop) ----
            let last_global = self.total_supply.saturating_sub(1);
            let global_index = self.tokens_index_of.get(id).unwrap_or(0);

            if global_index != last_global {
                if let Some(last_token) = self.tokens_index.get(last_global) {
                    self.tokens_index.insert(global_index, &last_token);
                    self.tokens_index_of.insert(&last_token, &global_index);
                }
            }
            self.tokens_index.remove(last_global);
            self.tokens_index_of.remove(id);
            self.total_supply = last_global;

            // ---- Ownership ledger ----
            self.token_owner.remove(id);
        }
    }

    // =========================================================================
    //  Tests (off-chain, `#[cfg(test)]`)
    // =========================================================================

    #[cfg(test)]
    mod tests {
        use super::*;

        fn default_accounts(
        ) -> ink::env::test::DefaultAccounts<ink::env::DefaultEnvironment> {
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

        fn charlie() -> AccountId {
            default_accounts().charlie
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
            assert_eq!(contract.balance_of(bob()), 1);
            assert_eq!(contract.owner_of(Id::U128(1)), Some(bob()));
        }

        #[ink::test]
        fn mint_emits_event() {
            set_caller(alice());
            let mut contract = CarbonCredit::new();
            let credit = sample_credit("Alpha Forest");
            let _ = contract.mint(bob(), credit);

            // Mint emits a standard PSP34 `Transfer` (None -> bob) plus the
            // domain-specific `CreditMinted` event.
            let recorded =
                ink::env::test::recorded_events().collect::<ink::prelude::vec::Vec<_>>();
            assert_eq!(recorded.len(), 2);
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
            assert_eq!(contract.balance_of(bob()), 0);
            assert_eq!(contract.owner_of(Id::U128(1)), None);
        }

        #[ink::test]
        fn burn_fails_for_non_owner() {
            set_caller(alice());
            let mut contract = CarbonCredit::new();
            let _ = contract.mint(bob(), sample_credit("Beta Wind"));

            set_caller(charlie());
            assert_eq!(contract.burn(1), Err(PSP34Error::NotApproved));
        }

        #[ink::test]
        fn burn_fails_for_missing_token() {
            set_caller(alice());
            let mut contract = CarbonCredit::new();
            assert_eq!(contract.burn(99), Err(PSP34Error::TokenNotExists));
        }

        #[ink::test]
        fn transfer_moves_ownership() {
            set_caller(alice());
            let mut contract = CarbonCredit::new();
            let _ = contract.mint(bob(), sample_credit("Gamma"));

            set_caller(bob());
            assert!(contract.transfer_credit(charlie(), 1).is_ok());
            assert_eq!(contract.owner_of(Id::U128(1)), Some(charlie()));
            assert_eq!(contract.balance_of(bob()), 0);
            assert_eq!(contract.balance_of(charlie()), 1);
        }

        #[ink::test]
        fn transfer_fails_when_not_approved() {
            set_caller(alice());
            let mut contract = CarbonCredit::new();
            let _ = contract.mint(bob(), sample_credit("Gamma"));

            set_caller(charlie());
            assert_eq!(
                contract.transfer(charlie(), Id::U128(1), Vec::new()),
                Err(PSP34Error::NotApproved)
            );
        }

        #[ink::test]
        fn approved_operator_can_transfer() {
            set_caller(alice());
            let mut contract = CarbonCredit::new();
            let _ = contract.mint(bob(), sample_credit("Gamma"));

            // Bob approves charlie for the specific token.
            set_caller(bob());
            assert!(contract
                .approve(charlie(), Some(Id::U128(1)), true)
                .is_ok());

            // Charlie can now move it.
            set_caller(charlie());
            assert!(contract
                .transfer(alice(), Id::U128(1), Vec::new())
                .is_ok());
            assert_eq!(contract.owner_of(Id::U128(1)), Some(alice()));
        }

        #[ink::test]
        fn approve_self_fails() {
            set_caller(alice());
            let mut contract = CarbonCredit::new();
            assert_eq!(
                contract.approve(alice(), None, true),
                Err(PSP34Error::SelfApprove)
            );
        }

        #[ink::test]
        fn enumerable_indices_track_tokens() {
            set_caller(alice());
            let mut contract = CarbonCredit::new();
            let _ = contract.mint(bob(), sample_credit("P1"));
            let _ = contract.mint(bob(), sample_credit("P2"));
            let _ = contract.mint(charlie(), sample_credit("P3"));

            assert_eq!(contract.total_supply(), 3);
            assert_eq!(contract.token_by_index(0), Some(Id::U128(1)));
            assert_eq!(contract.token_by_index(2), Some(Id::U128(3)));
            assert_eq!(
                contract.owners_token_by_index(bob(), 0),
                Some(Id::U128(1))
            );
            assert_eq!(
                contract.owners_token_by_index(bob(), 1),
                Some(Id::U128(2))
            );

            // Burn the first token; swap-and-pop should keep indices valid.
            set_caller(bob());
            let _ = contract.burn(1);
            assert_eq!(contract.total_supply(), 2);
            assert_eq!(contract.balance_of(bob()), 1);
            // Bob's remaining token is still reachable.
            assert_eq!(
                contract.owners_token_by_index(bob(), 0),
                Some(Id::U128(2))
            );
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
        fn get_credit_info_missing() {
            let contract = CarbonCredit::new();
            assert_eq!(
                contract.get_credit_info(42),
                Err(CarbonCreditError::TokenNotFound)
            );
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
