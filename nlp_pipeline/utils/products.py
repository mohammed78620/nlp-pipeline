from typing import List, Optional


class Products:
    @staticmethod
    def normalise_product(product: str) -> str:
        """
        Apply rules that ensure a product conforms to a particular standard i.e. uppercase, stripped whitespace

        Args:
            product (str): The product name to normalize

        Returns:
            str: The result
        """
        product = product.strip().upper()
        return product

    @staticmethod
    def normalise(products: List[str]) -> List[str]:
        """
        Normalize a list of products

        Args:
            products (List[str]): The list of products

        Returns:
            List[str]: The result
        """
        products = [Products.normalise_product(i) for i in products]
        return products

    @staticmethod
    def filter_product(product: str) -> Optional[str]:
        """
        Apply non-task specific product name filtering rules.

        Args:
            product (str): The product to apply filtering rules to.

        Returns:
            Optional[str]: The result. If filtered, result is None.
        """
        drop_conditions = ["\r", "\n", ":", "#", "[", "]"]
        min_char_length = 4
        max_char_length = 50
        max_tokens = 8

        if len(product) < min_char_length or len(product) > max_char_length:
            # Too short or too long
            return
        elif len(product.split(" ")) >= max_tokens:
            # Too many tokens
            return
        elif any([drop_condition in product for drop_condition in drop_conditions]):
            # Contains something suggesting it's not a good candidate
            return

        return product

    @staticmethod
    def filter(products: List[str]) -> List[str]:
        """
        Apply non-task specific product name filtering to list of products

        Args:
            products (List[str]): The list of products to filter

        Returns:
            List[str]: The result. If all products filtered, result will be an empty list.
        """
        # filter
        products = [product for product in products if Products.filter_product(product)]

        # unique
        products = list(set(products))
        return products

    @staticmethod
    def process(products: List[str]) -> List[str]:
        """
        Normalize and filter list of products

        Args:
            products (List[str]): The list of products to process

        Returns:
            List[str]: The result
        """
        products = Products.normalise(products)
        products = Products.filter(products)

        products.sort()
        return products
