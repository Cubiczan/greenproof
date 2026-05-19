//! # GreenVerify AI — Verifier Registry
//!
//! An **on-chain registry** of accounts that are authorised to verify carbon
//! credits on the GreenVerify AI platform.  Only the contract **owner** (the
//! deployer) may register, remove, or suspend verifiers.
//!
//! ## Purpose
//!
//! The CarbonCredit mint function checks this registry (off-chain or via
//! cross-contract call) to ensure that the `verifier` field in [`CreditData`]
//! belongs to an active, registered verifier — establishing a trust anchor
//! for the AI-powered verification pipeline.
//!
//! ## Data Model
//!
//! Each verifier is stored as a [`VerifierInfo`] struct keyed by their
//! `AccountId`.  Verifiers carry a human-readable name and an API endpoint
//! URL (for off-chain AI model lookup), plus an `active` flag that allows
//! the owner to temporarily suspend a verifier without deleting the record.
//!
//! ## Enumeration
//!
//! An internal `Mapping<u32, AccountId>` acts as a sparse index so that
//! [`get_all_verifiers`] can iterate through all registered accounts.

#![cfg_attr(not(feature = "std"), no_std)]

/// The verifier-registry contract.
#[ink::contract]
pub mod verifier_registry {

    // =========================================================================
    //  Types
    // =========================================================================

    /// Information stored for each registered verifier.
    #[derive(
        scale::Encode, scale::Decode, Clone, Debug, PartialEq, Eq,
    )]
    #[cfg_attr(
        feature = "std",
        derive(scale_info::TypeInfo, ink::storage::traits::StorageLayout)
    )]
    pub struct VerifierInfo {
        /// Human-readable verifier name / organisation.
        pub name: ink::prelude::string::String,
        /// URL of the verifier's AI verification API endpoint.
        pub api_endpoint: ink::prelude::string::String,
        /// Whether the verifier is currently active and allowed to verify.
        pub active: bool,
    }

    // =========================================================================
    //  Events
    // =========================================================================

    /// Emitted when a new verifier is added to the registry.
    #[ink(event)]
    pub struct VerifierRegistered {
        /// The verifier's account address.
        #[ink(topic)]
        pub account: AccountId,
        /// The name given at registration.
        pub name: ink::prelude::string::String,
    }

    /// Emitted when a verifier is permanently removed.
    #[ink(event)]
    pub struct VerifierRemoved {
        /// The verifier's account address.
        #[ink(topic)]
        pub account: AccountId,
    }

    /// Emitted when a verifier's `active` flag is toggled.
    #[ink(event)]
    pub struct VerifierStatusChanged {
        /// The verifier's account address.
        #[ink(topic)]
        pub account: AccountId,
        /// New active status.
        pub active: bool,
    }

    // =========================================================================
    //  Errors
    // =========================================================================

    /// Registry-specific error conditions.
    #[derive(Debug, PartialEq, Eq, scale::Encode, scale::Decode)]
    #[cfg_attr(feature = "std", derive(scale_info::TypeInfo))]
    pub enum RegistryError {
        /// Caller is not the contract owner.
        CallerNotOwner,
        /// The account is already registered.
        AlreadyRegistered,
        /// The account is not in the registry.
        NotRegistered,
    }

    // =========================================================================
    //  Storage
    // =========================================================================

    /// Registry contract state.
    #[ink(storage)]
    pub struct VerifierRegistry {
        /// Account that deployed this contract (sole admin).
        owner: AccountId,

        /// Core registry: `AccountId → VerifierInfo`.
        verifiers: Mapping<AccountId, VerifierInfo>,

        /// Sparse enumeration index: `index → AccountId`.
        verifier_index: Mapping<u32, AccountId>,

        /// Reverse lookup: `AccountId → index`.
        verifier_index_rev: Mapping<AccountId, u32>,

        /// Monotonic counter — total number of *ever registered* verifiers.
        verifier_count: u32,
    }

    // =========================================================================
    //  Constructor
    // =========================================================================

    impl VerifierRegistry {
        /// Creates a new, empty VerifierRegistry.
        ///
        /// The deployer (caller) is set as the owner.
        #[ink(constructor)]
        pub fn new() -> Self {
            Self {
                owner: Self::env().caller(),
                verifiers: Default::default(),
                verifier_index: Default::default(),
                verifier_index_rev: Default::default(),
                verifier_count: 0,
            }
        }
    }

    // =========================================================================
    //  Public Messages — Admin
    // =========================================================================

    impl VerifierRegistry {
        /// Returns the contract owner.
        #[ink(message)]
        pub fn owner(&self) -> AccountId {
            self.owner.clone()
        }
    }

    // =========================================================================
    //  Public Messages — Registry Management (owner only)
    // =========================================================================

    impl VerifierRegistry {
        /// Registers a new verifier.
        ///
        /// The verifier is created with `active = true`.
        ///
        /// # Errors
        /// - [`RegistryError::CallerNotOwner`]
        /// - [`RegistryError::AlreadyRegistered`]
        #[ink(message)]
        pub fn register_verifier(
            &mut self,
            account: AccountId,
            name: ink::prelude::string::String,
            api_endpoint: ink::prelude::string::String,
        ) -> Result<(), RegistryError> {
            self.ensure_owner();

            if self.verifiers.get(account).is_some() {
                return Err(RegistryError::AlreadyRegistered);
            }

            let info = VerifierInfo {
                name: name.clone(),
                api_endpoint,
                active: true,
            };

            // Store the verifier record.
            self.verifiers.insert(account, &info);

            // Update enumeration index.
            let idx = self.verifier_count;
            self.verifier_index.insert(idx, &account);
            self.verifier_index_rev.insert(account, &idx);
            self.verifier_count += 1;

            self.env().emit_event(VerifierRegistered { account, name });

            Ok(())
        }

        /// Permanently removes a verifier from the registry.
        ///
        /// # Errors
        /// - [`RegistryError::CallerNotOwner`]
        /// - [`RegistryError::NotRegistered`]
        #[ink(message)]
        pub fn remove_verifier(
            &mut self,
            account: AccountId,
        ) -> Result<(), RegistryError> {
            self.ensure_owner();

            if self.verifiers.get(account).is_none() {
                return Err(RegistryError::NotRegistered);
            }

            // Remove from the main mapping.
            self.verifiers.remove(account);

            self.env().emit_event(VerifierRemoved { account });

            Ok(())
        }

        /// Toggles a verifier's `active` status.
        ///
        /// Use this to **suspend** a verifier without deleting their record.
        ///
        /// # Errors
        /// - [`RegistryError::CallerNotOwner`]
        /// - [`RegistryError::NotRegistered`]
        #[ink(message)]
        pub fn update_verifier_status(
            &mut self,
            account: AccountId,
            active: bool,
        ) -> Result<(), RegistryError> {
            self.ensure_owner();

            let mut info = self
                .verifiers
                .get(account)
                .ok_or(RegistryError::NotRegistered)?;

            info.active = active;
            self.verifiers.insert(account, &info);

            self.env().emit_event(VerifierStatusChanged { account, active });

            Ok(())
        }
    }

    // =========================================================================
    //  Public Messages — Queries (any caller)
    // =========================================================================

    impl VerifierRegistry {
        /// Returns `true` if `account` is a registered verifier **and**
        /// currently active.
        #[ink(message)]
        pub fn is_verifier(&self, account: AccountId) -> bool {
            self.verifiers
                .get(account)
                .map(|info| info.active)
                .unwrap_or(false)
        }

        /// Returns the full [`VerifierInfo`] for a registered verifier.
        ///
        /// Returns `None` if the account is not in the registry.
        #[ink(message)]
        pub fn get_verifier(&self, account: AccountId) -> Option<VerifierInfo> {
            self.verifiers.get(account)
        }

        /// Returns **all** registered verifiers (active and inactive).
        ///
        /// NOTE: iterating through the full list is gas-intensive for large
        /// registries.  Use an off-chain indexer in production.
        #[ink(message)]
        pub fn get_all_verifiers(
            &self,
        ) -> ink::prelude::vec::Vec<(AccountId, VerifierInfo)> {
            let mut result = ink::prelude::vec::Vec::new();
            for i in 0..self.verifier_count {
                if let Some(account) = self.verifier_index.get(i) {
                    if let Some(info) = self.verifiers.get(account) {
                        result.push((account, info));
                    }
                }
            }
            result
        }
    }

    // =========================================================================
    //  Private Helpers
    // =========================================================================

    impl VerifierRegistry {
        /// Asserts that the caller is the contract owner; reverts otherwise.
        fn ensure_owner(&self) {
            assert_eq!(
                Self::env().caller(),
                self.owner,
                "VerifierRegistry: caller is not the owner"
            );
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

        fn alice() -> AccountId { default_accounts().alice }
        fn bob()   -> AccountId { default_accounts().bob }
        fn charlie() -> AccountId { default_accounts().charlie }

        fn new_registry() -> VerifierRegistry {
            set_caller(alice());
            VerifierRegistry::new()
        }

        #[ink::test]
        fn constructor_sets_owner() {
            let r = new_registry();
            assert_eq!(r.owner(), alice());
        }

        #[ink::test]
        fn register_and_query() {
            let mut r = new_registry();
            let _ = r.register_verifier(
                bob(),
                "EcoVerify AI".to_owned(),
                "https://api.ecoverify.ai".to_owned(),
            );
            assert!(r.is_verifier(bob()));
            let info = r.get_verifier(bob()).unwrap();
            assert_eq!(info.name, "EcoVerify AI");
            assert!(info.active);
        }

        #[ink::test]
        fn get_all_verifiers_works() {
            let mut r = new_registry();
            let _ = r.register_verifier(bob(), "A".to_owned(), "a.com".to_owned());
            let _ = r.register_verifier(charlie(), "B".to_owned(), "b.com".to_owned());
            let all = r.get_all_verifiers();
            assert_eq!(all.len(), 2);
        }

        #[ink::test]
        fn update_status_suspends_verifier() {
            let mut r = new_registry();
            let _ = r.register_verifier(bob(), "A".to_owned(), "a.com".to_owned());
            assert!(r.is_verifier(bob()));

            let _ = r.update_verifier_status(bob(), false);
            assert!(!r.is_verifier(bob()));

            // Re-activate.
            let _ = r.update_verifier_status(bob(), true);
            assert!(r.is_verifier(bob()));
        }

        #[ink::test]
        fn remove_verifier() {
            let mut r = new_registry();
            let _ = r.register_verifier(bob(), "A".to_owned(), "a.com".to_owned());
            let _ = r.remove_verifier(bob());
            assert!(!r.is_verifier(bob()));
            assert!(r.get_verifier(bob()).is_none());
        }

        #[ink::test]
        #[should_panic(expected = "caller is not the owner")]
        fn non_owner_cannot_register() {
            let mut r = new_registry();
            set_caller(bob());
            let _ = r.register_verifier(bob(), "X".to_owned(), "x.com".to_owned());
        }

        #[ink::test]
        fn double_register_fails() {
            let mut r = new_registry();
            let _ = r.register_verifier(bob(), "A".to_owned(), "a.com".to_owned());
            let err = r.register_verifier(bob(), "B".to_owned(), "b.com".to_owned());
            assert_eq!(err, Err(RegistryError::AlreadyRegistered));
        }

        #[ink::test]
        fn remove_nonexistent_fails() {
            let mut r = new_registry();
            let err = r.remove_verifier(bob());
            assert_eq!(err, Err(RegistryError::NotRegistered));
        }

        #[ink::test]
        fn events_are_emitted() {
            let mut r = new_registry();
            let _ = r.register_verifier(bob(), "A".to_owned(), "a.com".to_owned());

            let registered = r.env().emit_returned_events::<VerifierRegistered>();
            assert_eq!(registered.len(), 1);
            assert_eq!(registered[0].account, bob());
        }
    }
}
